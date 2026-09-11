"""Ekstrak PAA tersimpan dan siapkan query tambahan tanpa panggilan API."""

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path

from collect_paa import digest, extract_questions, read_json, write_csv, now
from prepare_original_queries import FIELDS as ORIGINAL_FIELDS, read_rows

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ORIGINAL_FIELDS + ['retrieval_query', 'retrieved_at', 'search_id', 'source_batch',
                           'parent_query_id', 'paa_depth', 'existing_match', 'n_source_occurrences',
                           'cross_domain_duplicate']
DECISION_FIELDS = ['query_id', 'language', 'status', 'reason', 'reviewer', 'reviewed_at']


def text_key(text):
    return ' '.join(text.casefold().split())


def check_id(value):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', value):
        raise ValueError('ID batch/ekspansi tidak valid.')
    return value


def source_record(row, parent='', depth=1):
    return {
        'query_id': 'query_' + digest(row['research_domain'] + '\n' + text_key(row['question'])),
        'query_text': row['question'], 'domain': row['research_domain'], 'language': 'unknown',
        'source_type': 'people_also_ask', 'source_record_id': row['paa_id'],
        'topic_id': row['topic_id'], 'source_reference': row['raw_path'],
        'source_file': row['raw_path'], 'used_in_technical_pilot': False,
        'retrieval_query': row['retrieval_query'], 'retrieved_at': row['retrieved_at'],
        'search_id': row['search_id'], 'source_batch': row['batch_id'],
        'parent_query_id': parent, 'paa_depth': depth,
    }


def build_pool(config, root=ROOT):
    """Read successful saved responses only; never rewrite the active main batch."""
    check_id(config['expansion_id'])
    records = []
    for batch in config['paa_batches']:
        check_id(batch)
        manifest_path = root / 'data/raw/paa/batches' / batch / 'manifest.json'
        if not manifest_path.exists():
            continue
        manifest = read_json(manifest_path)
        for job in manifest['jobs']:
            path = root / 'data/raw/paa/requests' / (job['request_id'] + '.json')
            if not path.exists():
                continue
            saved = read_json(path)
            if saved.get('status') not in {'success', 'no_paa'}:
                continue
            raw_path = path.relative_to(root).as_posix()
            for row in extract_questions(saved['response'], job, saved, raw_path):
                records.append(source_record(row))
    for batch in config['main_batches']:
        check_id(batch)
        for path in sorted((root / 'data/raw/main' / batch / 'queries').glob('*.json')):
            saved = read_json(path)
            google = saved.get('google', {})
            payload = google.get('response', {})
            if payload.get('search_metadata', {}).get('status') != 'Success':
                continue
            query = saved['query']
            search_id = payload.get('search_metadata', {}).get('id', '')
            job = {'request_id': digest(batch + ':' + query['query_id'] + ':' + search_id),
                   'topic_id': query['topic_id'], 'research_domain': query['domain'],
                   'source_text': query['query_text'], 'parameters': {'q': query['query_text']}}
            record = {'batch_id': batch, 'retrieved_at': google['started_at'], 'search_id': search_id}
            for row in extract_questions(payload, job, record, path.relative_to(root).as_posix()):
                # Current main sources are initial PAA (depth 1) or direct Trends (depth 0).
                parent_depth = int(query.get('paa_depth', 1 if query['source_type'] == 'people_also_ask' else 0))
                records.append(source_record(row, query['query_id'], parent_depth + 1))
    return list({r['source_record_id']: r for r in records}.values())


def prepare(config, changes=None, root=ROOT):
    records = build_pool(config, root)
    existing_path = (root / config['existing_pool']).resolve()
    existing_path.relative_to(root.resolve())
    existing = read_rows(existing_path)
    known_ids = {r['query_id'] for r in existing}
    known_texts = {text_key(r['query_text']) for r in existing}
    manual = root / 'data/manual' / (config['expansion_id'] + '_decisions.csv')
    saved = read_rows(manual) if manual.exists() else []
    if len({r['query_id'] for r in saved}) != len(saved):
        raise ValueError('ID keputusan duplikat.')
    decisions = {r['query_id']: r for r in saved}
    for query_id, change in (changes or {}).items():
        decisions[query_id] = {'query_id': query_id, 'reviewed_at': now(), **change}
    if set(decisions) - {r['query_id'] for r in records}:
        raise ValueError('Sumber keputusan hilang atau ID keputusan tidak dikenal.')
    for decision in decisions.values():
        if set(decision) != set(DECISION_FIELDS) or decision['status'] not in {'pending', 'accepted', 'needs_review', 'excluded'}:
            raise ValueError('Struktur/status keputusan tidak valid.')
        if decision['language'] not in {'id', 'en', 'unknown', 'other'}:
            raise ValueError('Kode bahasa tidak valid.')
        if decision['status'] != 'pending' and (not decision['reason'].strip() or not decision['reviewer'].strip()):
            raise ValueError('Alasan dan identitas penilai wajib diisi.')
        if decision['status'] == 'accepted' and decision['language'] != 'id':
            raise ValueError('Query diterima harus asli berbahasa Indonesia.')
    counts = Counter(r['query_id'] for r in records)
    domains = defaultdict(set)
    for row in records:
        domains[text_key(row['query_text'])].add(row['domain'])
    for row in records:
        decision = decisions.get(row['query_id'], {})
        row['language'] = decision.get('language', 'unknown')
        row['language_eligibility'] = 'eligible' if row['language'] == 'id' else 'deferred_language'
        row['selection_status'] = decision.get('status', 'pending')
        row['selection_reason'] = decision.get('reason', 'Belum ditinjau bahasa dan kualitasnya.')
        row['existing_match'] = 'query_id' if row['query_id'] in known_ids else ('text_other_domain' if text_key(row['query_text']) in known_texts else '')
        row['n_source_occurrences'] = counts[row['query_id']]
        row['cross_domain_duplicate'] = len(domains[text_key(row['query_text'])]) > 1
        if row['existing_match']:
            row['selection_status'] = 'already_in_existing_pool'
            row['selection_reason'] = 'Teks sudah ada dalam pool awal; keputusan dan batch awal tetap dipertahankan.'
        elif row['cross_domain_duplicate'] and row['selection_status'] == 'accepted':
            row['selection_status'] = 'needs_review'
            row['selection_reason'] = 'Teks sama muncul pada domain berbeda; tentukan domain sebelum menerima.'
    output = root / 'data/interim/query_expansion' / config['expansion_id']
    unique = list({r['query_id']: r for r in records}.values())
    candidates = [r for r in unique if not r['existing_match']]
    for name, rows in [('source_pool', records), ('candidates', candidates),
                       ('already_known', [r for r in unique if r['existing_match']]),
                       ('accepted_new', [r for r in candidates if r['selection_status'] == 'accepted']),
                       ('pending', [r for r in candidates if r['selection_status'] == 'pending']),
                       ('needs_review', [r for r in candidates if r['selection_status'] == 'needs_review']),
                       ('excluded', [r for r in candidates if r['selection_status'] == 'excluded'])]:
        write_csv(output / (name + '.csv'), rows, FIELDS)
    write_csv(manual, list(decisions.values()), DECISION_FIELDS)
    print('Kemunculan PAA:', len(records), '| query unik dengan domain:', len(unique))
    print('Kandidat baru:', len(candidates), dict(Counter(r['domain'] for r in candidates)))
    print('Status:', dict(Counter(r['selection_status'] for r in candidates)))
    print('Output:', output)
    return candidates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/query_expansion_01.json')
    args = parser.parse_args()
    prepare(read_json(args.config))


if __name__ == '__main__':
    main()
