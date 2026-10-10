"""Pilih query PAA accepted untuk batch utama baru secara berimbang dan tercatat.

Contoh:
    python src/select_main_batch_queries.py --batch-id main_04
    python src/select_main_batch_queries.py --batch-id main_04 --run

Pratinjau tidak menulis berkas. Pemilihan lokal ini tidak memanggil API.
"""

import argparse
import csv
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / 'data/interim/query_expansion/query_expansion_01/accepted_unused_20261009.csv'
DOMAINS = ('kesehatan', 'keuangan', 'teknologi')


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames, list(reader)


def select(rows, count_per_domain, seed):
    if count_per_domain < 1:
        raise ValueError('Jumlah per domain harus positif.')
    ids = [row['query_id'] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('ID query kandidat ganda.')
    if not all(row['selection_status'] == 'accepted' and row['language'] == 'id'
               and row['source_type'] == 'people_also_ask' for row in rows):
        raise ValueError('Kandidat harus berupa PAA Indonesia dengan keputusan accepted.')
    if {row['domain'] for row in rows} != set(DOMAINS):
        raise ValueError('Kandidat harus memuat ketiga domain penelitian.')
    picked = {}
    for domain in DOMAINS:
        candidates = [row for row in rows if row['domain'] == domain]
        if len(candidates) < count_per_domain:
            raise ValueError(f'Kandidat {domain} hanya {len(candidates)}.')
        groups = defaultdict(list)
        for row in candidates:
            if not row['topic_id']:
                raise ValueError(f'Topik asal kosong: {row["query_id"]}')
            groups[row['topic_id']].append(row)
        rng = random.Random(f'{seed}:{domain}')
        topics = sorted(groups)
        rng.shuffle(topics)
        for topic in topics:
            groups[topic].sort(key=lambda row: row['query_id'])
            rng.shuffle(groups[topic])
        chosen = []
        # Satu pertanyaan dari tiap topik dahulu, lalu putaran berikutnya.
        while len(chosen) < count_per_domain:
            made_progress = False
            for topic in topics:
                if groups[topic]:
                    chosen.append(groups[topic].pop())
                    made_progress = True
                    if len(chosen) == count_per_domain:
                        break
            if not made_progress:
                raise ValueError(f'Kandidat {domain} tidak mencukupi.')
        picked[domain] = chosen
    # Urutan batch juga berimbang jika kelak diproses bertahap.
    return [picked[domain][index] for index in range(count_per_domain)
            for domain in DOMAINS]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch-id', required=True,
                        help='ID batch baru, misalnya main_04.')
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--count-per-domain', type=int, default=15)
    parser.add_argument('--seed', type=int, default=20261009)
    parser.add_argument('--run', action='store_true', help='Simpan CSV dan catatan pemilihan.')
    args = parser.parse_args()
    if not re.fullmatch(r'main_[0-9]{2,}', args.batch_id):
        parser.error('--batch-id harus berbentuk main_04 atau nomor berikutnya.')
    if args.count_per_domain < 1:
        parser.error('--count-per-domain harus positif.')
    source = args.source.resolve()
    source.relative_to(ROOT.resolve())
    fieldnames, rows = read_csv(source)
    reserved_ids = set()
    reserved_texts = set()
    for snapshot in sorted((ROOT / 'data/manual').glob('main_*_queries.csv')):
        if snapshot.name == f'{args.batch_id}_queries.csv' or not snapshot.stat().st_size:
            continue
        _, used_rows = read_csv(snapshot)
        for used in used_rows:
            reserved_ids.add(used['query_id'])
            reserved_texts.add((used['domain'], ' '.join(used['query_text'].casefold().split())))
    available = [row for row in rows if row['query_id'] not in reserved_ids
                 and (row['domain'], ' '.join(row['query_text'].casefold().split())) not in reserved_texts]
    selected = select(available, args.count_per_domain, args.seed)
    output = ROOT / 'data/manual' / f'{args.batch_id}_queries.csv'
    record = ROOT / 'configs' / f'{args.batch_id}_query_selection.json'
    manifest = ROOT / 'data/raw/main' / args.batch_id / 'manifest.json'
    print('Kandidat sumber:', len(rows), '| belum terjadwal:', len(available), '| pilihan:', len(selected),
          dict(Counter(row['domain'] for row in selected)))
    print('Topik asal terwakili:', dict(Counter({domain: len({row['topic_id'] for row in selected
                                                     if row['domain'] == domain}) for domain in DOMAINS})))
    print('CSV:', output.relative_to(ROOT))
    print('Catatan:', record.relative_to(ROOT))
    if not args.run:
        print('Pratinjau saja; tambahkan --run untuk menyimpan.')
        return
    if manifest.exists():
        raise ValueError('Manifest batch sudah dibuat; pilihan query telah dibekukan.')
    if record.exists() or (output.exists() and output.stat().st_size > 0):
        raise FileExistsError('Berkas batch sudah berisi data; pilih ID baru atau periksa berkas lama.')
    previous_ids = set()
    previous_texts = set()
    for path in sorted((ROOT / 'data/raw/main').glob('*/manifest.json')):
        for query in json.loads(path.read_text(encoding='utf-8'))['queries']:
            previous_ids.add(query['query_id'])
            previous_texts.add((query['domain'], ' '.join(query['query_text'].casefold().split())))
    for row in selected:
        if row['query_id'] in previous_ids or (row['domain'], ' '.join(row['query_text'].casefold().split())) in previous_texts:
            raise ValueError(f'Query sudah terjadwal: {row["query_id"]}')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(selected)
    record.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        'selection_version': f'{args.batch_id}_topic_balanced_seeded_v1',
        'selected_at': datetime.now(timezone.utc).isoformat(),
        'source': source.relative_to(ROOT).as_posix(),
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'available_after_existing_snapshots': len(available),
        'method': 'Accepted PAA; jumlah sama per domain; topik asal diputar sebelum pengulangan, urutan kandidat diacak dengan seed tetap.',
        'count_per_domain': args.count_per_domain,
        'seed': args.seed,
        'query_ids_in_order': [row['query_id'] for row in selected],
        'query_texts_in_order': [row['query_text'] for row in selected],
    }
    record.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Tersimpan. Tinjau CSV sebelum membuat manifest pengumpulan.')


if __name__ == '__main__':
    main()
