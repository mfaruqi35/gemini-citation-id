"""Recover saved source redirects without regenerating answers or changing raw data."""
import argparse
import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from collect_paa import read_json, write_json, now
from collect_main_dataset import trial_info, organic_rows
from pilot_gemini_grounding import destination_url, resolve_url

ROOT = Path(__file__).resolve().parents[1]
CACHE = 'data/interim/article_repair/url_resolutions.json'


def missing_sources(batches, root=ROOT):
    """Deduplicate requests and retain the raw record identity for audit."""
    missing = {}
    for batch in batches:
        for path in sorted((root / 'data/raw/main' / batch / 'queries').glob('*.json')):
            record = read_json(path)
            google = record.get('google', {})
            for item in organic_rows(google):
                url = item['link']
                if not destination_url(google.get('url_resolutions', {}).get(url, {})):
                    missing.setdefault(url, []).append(str(path.relative_to(root)))
            for trial in record.get('trials', []):
                valid, _, _, web, cited = trial_info(trial)
                if valid:
                    for index in cited:
                        url = web[index]['uri']
                        if not destination_url(trial.get('url_resolutions', {}).get(url, {})):
                            missing.setdefault(url, []).append(str(path.relative_to(root)))
    return missing


def recover(batches, root=ROOT, run=False, limit=100, retry_failed=False, resolver=resolve_url):
    path = root / CACHE
    cache = read_json(path) if path.exists() else {}
    missing = missing_sources(batches, root)
    todo = [u for u in missing if u not in cache or
            (retry_failed and not destination_url(cache[u]))][:limit]
    print(f'Resolusi URL saja: {len(missing)} URL sumber belum diketahui pada raw; '
          f'{len(todo)} dijadwalkan. Tanpa panggilan Gemini/SerpApi.', flush=True)
    if not run:
        print('Preview saja; tambahkan --run untuk akses redirect.', flush=True)
        return cache
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix('.lock')
    with lock_path.open('x', encoding='utf-8') as lock:
        try:
            # Results are committed serially; requests are bounded and independent.
            with ThreadPoolExecutor(max_workers=3) as pool:
                for index, (url, result) in enumerate(zip(todo, pool.map(resolver, todo)), 1):
                    old = cache.get(url)
                    result['source_records'] = sorted(set(missing[url]))
                    result['recovery_history'] = ([old] if old else [])
                    result['recovered_at'] = now()
                    cache[url] = result
                    write_json(path, cache)
                    print(f"{index}/{len(todo)} | {result['resolution_status']} | "
                          f"{hashlib.sha256(url.encode()).hexdigest()[:12]}", flush=True)
        finally:
            lock.close()
            lock_path.unlink(missing_ok=True)
    return cache


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batches', nargs='+', default=['main_01', 'main_02'])
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--retry-failed', action='store_true')
    parser.add_argument('--max-new-urls', type=int, default=100)
    args = parser.parse_args()
    if args.max_new_urls < 1 or any(not b.replace('_', '').isalnum() for b in args.batches):
        parser.error('Nama batch atau batas URL tidak valid.')
    recover(args.batches, run=args.run, limit=args.max_new_urls, retry_failed=args.retry_failed)


if __name__ == '__main__':
    main()
