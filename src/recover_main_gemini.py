"""Bounded Gemini recovery and continuation using saved Google checkpoints."""
import argparse
import os
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from collect_main_dataset import ROOT, make_manifest, export_dataset
from collect_paa import read_json, write_json, now, digest
from pilot_gemini_grounding import generate, GenerationError, load_key, grounding, resolve_url

RETRYABLE = {'network_or_timeout', 'timeout', 'network_error', '503'}


def collection_window_reason(record, config):
    google = record.get('google', {})
    if google.get('status') != 'completed':
        return 'google_not_completed'
    try:
        timestamps = [datetime.fromisoformat(google['started_at'])]
        timestamps += [datetime.fromisoformat(t['started_at']) for t in record['trials']]
        timestamps.append(datetime.fromisoformat(now()))
        gap = (max(timestamps) - min(timestamps)).total_seconds() / 3600
    except (KeyError, TypeError, ValueError):
        return 'invalid_collection_timestamp'
    return 'ready' if gap <= config['max_collection_gap_hours'] else 'collection_window_expired'


def recovery_reason(record, trial, config, finish_incomplete=False):
    if trial is None:
        return collection_window_reason(record, config) if finish_incomplete else 'not_requested'
    if trial.get('status') == 'response_saved' and (trial.get('recovery_history') or finish_incomplete):
        return 'resume_resolution'
    if trial.get('status') != 'error' or trial.get('error') not in RETRYABLE:
        return 'not_transport_error'
    if trial.get('response'):
        return 'response_already_saved'
    if trial.get('recovery_history'):
        return 'retry_limit_reached'
    return collection_window_reason(record, config)


def slots(record, config, finish_incomplete):
    if not finish_incomplete:
        return [(t['repetition'], t) for t in record.get('trials', [])]
    return [(n, next((t for t in record.get('trials', []) if t['repetition'] == n), None))
            for n in range(1, config['repetitions'] + 1)]


def preview(manifest, data_root, finish_incomplete=False):
    raw = data_root / 'raw/main' / manifest['config']['dataset_id']
    rows = []
    for query in manifest['queries']:
        path = raw / 'queries' / (query['query_id'] + '.json')
        if not path.exists():
            continue
        record = read_json(path)
        uncertain = any(t.get('status') == 'started' for t in record.get('trials', []))
        for repetition, trial in slots(record, manifest['config'], finish_incomplete):
            if trial is None or trial.get('error') in RETRYABLE or trial.get('recovery_history') or (
                    finish_incomplete and trial.get('status') in {'started', 'response_saved'}):
                rows.append({'query_id': query['query_id'], 'query_text': query['query_text'],
                             'repetition': repetition,
                             'action': 'new_slot' if trial is None else 'recover_or_resume',
                             'recovery_status': 'uncertain_trial_checkpoint' if uncertain else
                             recovery_reason(record, trial, manifest['config'], finish_incomplete)})
    return rows


def recover(manifest, data_root, key, max_new_calls=3, query_id=None,
            generator=generate, resolver=resolve_url, finish_incomplete=False):
    if max_new_calls < 1:
        raise ValueError('max_new_calls harus positif.')
    config = manifest['config']
    raw = data_root / 'raw/main' / config['dataset_id']
    if read_json(raw / 'manifest.json') != manifest:
        raise ValueError('Manifest berbeda dari batch tersimpan.')
    if query_id and not any(q['query_id'] == query_id for q in manifest['queries']):
        raise ValueError('Query tidak ditemukan pada manifest.')
    lock = raw / 'running.lock'
    with lock.open('x') as handle:
        handle.write(str(os.getpid()))
    calls = 0
    try:
        for query in manifest['queries']:
            if query_id and query['query_id'] != query_id:
                continue
            path = raw / 'queries' / (query['query_id'] + '.json')
            if not path.exists():
                continue
            if path.with_suffix('.tmp').exists():
                raise ValueError('Checkpoint .tmp masih ada; periksa sebelum recovery agar respons tidak hilang.')
            record = read_json(path)
            if record.get('query') != query:
                raise ValueError('Identitas query checkpoint berbeda.')
            if any(t.get('status') == 'started' for t in record.get('trials', [])):
                print('Recovery dilewati:', query['query_text'], 'uncertain_trial_checkpoint', flush=True)
                continue
            for repetition, trial in slots(record, config, finish_incomplete):
                reason = recovery_reason(record, trial, config, finish_incomplete)
                if reason not in {'ready', 'resume_resolution'}:
                    if trial is None or trial.get('error') in RETRYABLE:
                        print('Recovery dilewati:', query['query_text'], repetition, reason, flush=True)
                    continue
                if reason == 'ready':
                    if calls >= max_new_calls:
                        continue
                    if trial is None:
                        trial = {'trial_id': 'main_trial_' + digest(config['dataset_id'] + query['query_id'] + str(repetition)),
                                 'repetition': repetition, 'status': 'started', 'started_at': now(),
                                 'transport_timeout_seconds': 120}
                        record.setdefault('trials', []).append(trial)
                    else:
                        previous = deepcopy(trial)
                        trial.clear()
                        trial.update(trial_id=previous['trial_id'], repetition=previous['repetition'],
                                     status='started', started_at=now(), transport_timeout_seconds=120,
                                     recovery_history=[{'archived_at': now(), 'trial': previous}],
                                     recovery_policy='transport_or_503_one_retry_v2')
                    record['status'] = 'started'
                    write_json(path, record)
                    request = {'contents': [{'role': 'user', 'parts': [{'text': query['query_text']}]}],
                               'tools': [{'google_search': {}}],
                               'systemInstruction': {'parts': [{'text': config['system_instruction']}]},
                               'generationConfig': config['generation_config']}
                    calls += 1
                    print('Recovery Gemini:', query['query_text'], '| percobaan', trial['repetition'], flush=True)
                    try:
                        trial['response'] = generator(config['model'], request, key)
                    except GenerationError as error:
                        trial.update(status='error', error=error.code, error_details=error.details,
                                     failed_at=now())
                        record['status'] = ('completed' if len(record['trials']) == config['repetitions']
                                            and all(t['status'] in {'completed', 'error'} for t in record['trials'])
                                            else 'started')
                        write_json(path, record)
                        raise
                    trial['status'] = 'response_saved'
                    write_json(path, record)
                _, _, web, _, _ = grounding(trial['response'])
                resolutions = trial.setdefault('url_resolutions', {})
                for url in dict.fromkeys(source['uri'] for source in web.values()):
                    if url not in resolutions:
                        resolutions[url] = resolver(url)
                        write_json(path, record)
                trial.update(status='completed', completed_at=now())
                record['status'] = ('completed' if len(record['trials']) == config['repetitions']
                                    and all(t['status'] in {'completed', 'error'} for t in record['trials'])
                                    else 'started')
                write_json(path, record)
        print('Recovery selesai. Panggilan Gemini baru:', calls, '| pencarian SerpApi: 0', flush=True)
        return calls
    finally:
        try:
            export_dataset(manifest, data_root)
        finally:
            lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/main_dataset_02.json')
    parser.add_argument('--query-id')
    parser.add_argument('--max-new-calls', type=int, default=3)
    parser.add_argument('--finish-incomplete', action='store_true',
                        help='Isi juga slot yang belum dimulai pada query dengan Google tersimpan; tanpa pencarian baru.')
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.max_new_calls < 1:
        parser.error('--max-new-calls harus positif.')
    manifest = make_manifest(read_json(args.config))
    for row in preview(manifest, ROOT / 'data', args.finish_incomplete):
        if not args.query_id or args.query_id == row['query_id']:
            print(row, flush=True)
    if args.run:
        recover(manifest, ROOT / 'data', load_key(), args.max_new_calls, args.query_id,
                finish_incomplete=args.finish_incomplete)
    else:
        print('Preview lokal. --run memakai Gemini; timeout lama mungkin sudah ditagihkan oleh penyedia.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, OSError) as error:
        print(str(error), flush=True)
        raise SystemExit(1)
