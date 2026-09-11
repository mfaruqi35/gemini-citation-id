"""Pulihkan satu pencarian Google yang gagal; tidak memanggil Gemini."""

import argparse
import os
from pathlib import Path

from collect_paa import read_json, write_json, now, quota, fetch, sanitize
from collect_main_dataset import ROOT, get_serp_key, export_dataset, make_manifest


def recover(manifest, data_root, query_id, key, fetcher=fetch, quota_reader=quota):
    config = manifest['config']
    raw = data_root / 'raw/main' / config['dataset_id']
    selected = [q for q in manifest['queries'] if q['query_id'] == query_id]
    if len(selected) != 1:
        raise ValueError('Query tidak ditemukan pada manifest.')
    path = raw / 'queries' / (query_id + '.json')
    lock = raw / 'running.lock'
    with lock.open('x') as handle:
        handle.write(str(os.getpid()))
    try:
        if read_json(raw / 'manifest.json') != manifest:
            raise ValueError('Manifest berbeda dari batch tersimpan.')
        record = read_json(path)
        if record.get('query') != selected[0]:
            raise ValueError('Identitas query checkpoint berbeda.')
        google = record['google']
        if google['status'] in {'completed', 'response_saved'}:
            print('Respons Google sudah tersimpan; tidak ada pencarian baru.')
            return record
        if google['status'] not in {'started', 'error'} or google.get('response') or record.get('trials'):
            raise ValueError('Pemulihan ini hanya untuk Google gagal tanpa respons dan tanpa percobaan Gemini.')
        if path.with_suffix('.tmp').exists():
            raise ValueError('Ada file .tmp; periksa checkpoint sementara sebelum mengulang pencarian.')
        account = quota_reader(key)
        if account['total_searches_left'] < 1 + config['serp_quota_reserve']:
            raise RuntimeError('Kuota tidak cukup untuk satu permintaan dan cadangan.')
        history = record.setdefault('google_recovery_history', [])
        history.append({'archived_at': now(), 'google': google, 'quota_before': account,
                        'note': 'Explicit single-request recovery with identical parameters and default cache enabled.'})
        record['google'] = {'status': 'started', 'started_at': now(), 'recovery_attempt': len(history)}
        write_json(path, record)
        try:
            payload = sanitize(fetcher('search.json', {**config['google_parameters'],
                                                      'q': selected[0]['query_text']}, key), key)
            record['google']['response'] = payload
            if payload.get('error') or payload.get('search_metadata', {}).get('status') != 'Success':
                raise RuntimeError('Google Search belum berhasil; respons disimpan untuk diperiksa.')
            if payload.get('search_parameters', {}).get('q') != selected[0]['query_text']:
                raise ValueError('Query respons berbeda; checkpoint perlu diperiksa.')
            record['google']['status'] = 'response_saved'
            record['google']['response_received_at'] = now()
            # Retain the observed search timestamp when recovery returns a cached response.
            created = payload.get('search_metadata', {}).get('created_at')
            if created:
                from datetime import datetime, timezone
                try:
                    timestamp = datetime.strptime(created, '%Y-%m-%d %H:%M:%S UTC').replace(tzinfo=timezone.utc)
                    record['google']['started_at'] = timestamp.isoformat()
                except ValueError:
                    # Conservatively retain the initial attempt time if cache age is unknown.
                    record['google']['started_at'] = history[0]['google']['started_at']
            else:
                record['google']['started_at'] = history[0]['google']['started_at']
        except (RuntimeError, ValueError) as error:
            record['google']['status'] = 'error'
            record['google']['error_code'] = getattr(error, 'code', 'search_error')
            record['google']['error_details'] = getattr(error, 'details', {})
            write_json(path, record)
            export_dataset(manifest, data_root)
            raise
        write_json(path, record)
        try:
            record['google']['recovery_quota_after'] = quota_reader(key)
            write_json(path, record)
        except RuntimeError:
            print('Respons tersimpan; kuota akhir belum dapat diperiksa.')
        export_dataset(manifest, data_root)
        print('Google berhasil dipulihkan:', selected[0]['query_text'], '| Gemini: 0 panggilan.')
        return record
    finally:
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/main_dataset.json')
    parser.add_argument('--query-id', required=True)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    manifest = make_manifest(read_json(args.config))
    if not args.run:
        print('Pratinjau pemulihan:', args.query_id,
              '| Tambahkan --run untuk satu permintaan Google; cache dapat digunakan jika tersedia.')
        return
    recover(manifest, ROOT / 'data', args.query_id,
            get_serp_key(manifest['config']['serp_api_key_variable']))


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, FileExistsError) as error:
        print(str(error))
        raise SystemExit(1)
