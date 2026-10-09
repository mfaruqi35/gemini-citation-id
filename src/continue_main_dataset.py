"""Prepare remaining accepted queries and collect with periodic quota/usage checks."""
import argparse
from collections import Counter
from pathlib import Path

from collect_main_dataset import ROOT, read_rows, make_manifest, collect, get_serp_key
from collect_paa import read_json, write_json, write_csv, quota, now
from pilot_gemini_grounding import load_key


def prepare(config_path=None):
    if config_path is not None:
        path = (ROOT / config_path).resolve()
        path.relative_to(ROOT.resolve())
        if not path.exists():
            raise ValueError(f'Konfigurasi batch tidak ditemukan: {config_path}')
        return make_manifest(read_json(path))
    config_path = ROOT / 'configs/main_dataset_02.json'
    target = ROOT / 'data/manual/main_02_queries.csv'
    if config_path.exists():
        return make_manifest(read_json(config_path))
    if target.exists():
        raise ValueError('Snapshot main_02 sudah ada tanpa config; periksa sebelum melanjutkan.')
    used_ids, used_texts = set(), set()
    for path in (ROOT / 'data/raw/main').glob('*/manifest.json'):
        for row in read_json(path)['queries']:
            used_ids.add(row['query_id'])
            used_texts.add(' '.join(row['query_text'].casefold().split()))
    rows = []
    for source in ('data/interim/original_queries/accepted_unique.csv',
                   'data/interim/query_expansion/query_expansion_01/accepted_new.csv'):
        for row in read_rows(ROOT / source):
            key = ' '.join(row['query_text'].casefold().split())
            if (row['selection_status'] != 'accepted' or row['language'] != 'id'
                    or row['query_id'] in used_ids or key in used_texts):
                continue
            rows.append(row)
            used_ids.add(row['query_id'])
            used_texts.add(key)
    if not rows:
        raise ValueError('Tidak ada query accepted baru.')
    fields = list(dict.fromkeys(k for row in rows for k in row))
    write_csv(target, rows, fields)
    config = read_json(ROOT / 'configs/main_dataset.json')
    config.update(dataset_id='main_02', query_csv='data/manual/main_02_queries.csv',
                  max_serp_searches=len(rows), citation_threshold=0.5)
    write_json(config_path, config)
    return make_manifest(config)


def usage(raw):
    counts = Counter()
    for path in (raw / 'queries').glob('*.json'):
        record = read_json(path)
        counts['query_records'] += 1
        counts['completed_queries'] += record.get('status') == 'completed'
        for trial in record.get('trials', []):
            counts['trial_records'] += 1
            counts['error_trials'] += trial.get('status') == 'error'
            counts['archived_failed_attempts'] += len(trial.get('recovery_history', []))
            payload = trial.get('response', {})
            counts['responses_with_usage'] += bool(payload.get('usageMetadata'))
            for field, value in payload.get('usageMetadata', {}).items():
                if field.endswith('TokenCount') and isinstance(value, int):
                    counts[field] += value
    return dict(counts)


def monitor(raw, key):
    report = {'checked_at': now(), 'gemini_usage_this_batch': usage(raw),
              'gemini_balance': 'not_available_from_generate_content_api',
              'serpapi': quota(key)}
    write_json(raw / 'usage_latest.json', report)
    stamp = report['checked_at'].replace(':', '').replace('+', '_')
    write_json(raw / 'usage_history' / (stamp + '.json'), report)
    print('Pemantauan:', report, flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path,
                        help='Konfigurasi batch utama yang akan dipantau/dilanjutkan; default tetap main_02.')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--max-queries', type=int, default=265)
    parser.add_argument('--check-every', type=int, default=5)
    parser.add_argument('--quota-reserve', type=int, default=None,
                        help='Cadangan SerpApi untuk eksekusi ini; tidak mengubah manifest batch.')
    parser.add_argument('--unstarted-only', action='store_true', help='Hanya query tanpa checkpoint; lewati seluruh query yang pernah dimulai.')
    parser.add_argument('--recover-gemini', action='store_true', help='Pulihkan error transport sebelum query baru; satu retry per slot.')
    parser.add_argument('--max-recovery-calls', type=int, default=3)
    args = parser.parse_args()
    if args.max_queries < 1 or args.check_every < 1 or args.max_recovery_calls < 1:
        parser.error('Batas query dan interval pemeriksaan harus positif.')
    if args.quota_reserve is not None and args.quota_reserve < 0:
        parser.error('--quota-reserve harus bilangan bulat nonnegatif.')
    if args.unstarted_only and args.recover_gemini:
        parser.error('--unstarted-only tidak boleh digabung dengan --recover-gemini.')
    manifest = prepare(args.config)
    config = manifest['config']
    reserve = config['serp_quota_reserve'] if args.quota_reserve is None else args.quota_reserve
    raw = ROOT / 'data/raw/main' / config['dataset_id']
    print('Batch:', config['dataset_id'], '| Query:', len(manifest['queries']),
          dict(Counter(q['domain'] for q in manifest['queries'])), flush=True)
    if args.unstarted_only:
        unstarted = sum(not (raw / 'queries' / (q['query_id'] + '.json')).exists()
                        for q in manifest['queries'])
        print('Mode hanya query baru; belum dimulai:', unstarted, flush=True)
    if args.quota_reserve is not None:
        print('Cadangan SerpApi eksekusi ini:', reserve,
              '| cadangan pada manifest:', config['serp_quota_reserve'], flush=True)
    if not args.run:
        if args.recover_gemini:
            from recover_main_gemini import preview
            for row in preview(manifest, ROOT / 'data'):
                print(row, flush=True)
        print('Snapshot siap; belum ada panggilan API. Tambahkan --run untuk melanjutkan.')
        return
    serp_key, gemini_key = get_serp_key(config['serp_api_key_variable']), load_key()
    if args.recover_gemini:
        from recover_main_gemini import recover
        monitor(raw, serp_key)
        try:
            recover(manifest, ROOT / 'data', gemini_key, args.max_recovery_calls)
        finally:
            try:
                monitor(raw, serp_key)
            except (RuntimeError, OSError):
                print('Kuota akhir recovery belum dapat diperiksa; checkpoint tetap tersimpan.', flush=True)
    processed = 0
    while processed < args.max_queries:
        report = monitor(raw, serp_key)
        remaining = []
        for q in manifest['queries']:
            path = raw / 'queries' / (q['query_id'] + '.json')
            if args.unstarted_only and path.exists():
                continue
            if not path.exists() or read_json(path).get('status') != 'completed':
                remaining.append(q)
        if not remaining:
            print('Tidak ada query baru yang belum dimulai.' if args.unstarted_only else 'Semua query batch selesai.', flush=True)
            return
        available = max(0, report['serpapi']['total_searches_left'] - reserve)
        selected = 0
        for q in remaining[:min(args.check_every, args.max_queries - processed)]:
            exists = (raw / 'queries' / (q['query_id'] + '.json')).exists()
            if not exists and available <= 0:
                break
            available -= not exists
            selected += 1
        if not selected:
            print('Berhenti pada cadangan kuota SerpApi. Query tersisa:', len(remaining), flush=True)
            return
        try:
            extra = ({'quota_reserve_override': reserve} if args.quota_reserve is not None else {})
            collect(manifest, ROOT / 'data', serp_key, gemini_key, max_queries=selected,
                    unstarted_only=args.unstarted_only, **extra)
        except (RuntimeError, ValueError, OSError):
            try:
                monitor(raw, serp_key)
            except (RuntimeError, OSError):
                print('Pemeriksaan kuota akhir gagal; respons dan token tetap ada di checkpoint.', flush=True)
            raise
        processed += selected
    monitor(raw, serp_key)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, OSError) as error:
        print(str(error), flush=True)
        raise SystemExit(1)
