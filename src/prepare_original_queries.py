"""Siapkan kandidat query asli tanpa API, parafrasa, atau penerjemahan."""

import csv
import json
from collections import Counter
from pathlib import Path

from collect_paa import digest, read_json, write_csv

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["query_id", "query_text", "domain", "language", "source_type", "source_record_id",
          "topic_id", "source_reference", "source_file", "language_eligibility", "selection_status",
          "selection_reason", "used_in_technical_pilot"]
DECISION_FIELDS = ["query_id", "status", "reason"]


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_pool():
    config = read_json(ROOT / 'configs/original_query_sources.json')
    pilot_ids = set(read_json(ROOT / 'configs/gemini_grounding_pilot.json')['paa_ids'])
    records = []
    paa_path = ROOT / config['paa_csv']
    for row in read_rows(paa_path):
        language = config['paa_language_review'].get(row['paa_id'], 'unknown')
        records.append({
            'query_text': row['question'], 'domain': row['research_domain'], 'language': language,
            'source_type': 'people_also_ask', 'source_record_id': row['paa_id'], 'topic_id': row['topic_id'],
            'source_reference': row['raw_path'], 'source_file': config['paa_csv'],
            'used_in_technical_pilot': row['paa_id'] in pilot_ids,
        })
    trends_path = ROOT / config['trends_review_csv']
    for row in read_rows(trends_path):
        if row['status'] != 'ready_for_synthesis':
            continue
        # Legacy readiness is only used to identify sufficiently specific source texts.
        records.append({
            'query_text': row['source_text'], 'domain': row['research_domain'], 'language': row['language'],
            'source_type': 'google_trends', 'source_record_id': row['topic_id'], 'topic_id': row['topic_id'],
            'source_reference': row['source_files'], 'source_file': config['trends_review_csv'],
            'used_in_technical_pilot': False,
        })
    for row in records:
        # Text and provenance remain unchanged; normalization is only for the identifier.
        row['query_id'] = 'query_' + digest(row['domain'] + '\n' + ' '.join(row['query_text'].casefold().split()))
        row['language_eligibility'] = 'eligible' if row['language'] == 'id' else 'deferred_language'
        row['selection_status'] = 'pending' if row['language'] == 'id' else 'deferred_language'
        row['selection_reason'] = '' if row['language'] == 'id' else 'Belum masuk jalur query asli berbahasa Indonesia; teks asli tetap disimpan.'
    return records


def prepare(decisions=None):
    records = build_pool()
    manual_path = ROOT / 'data/manual/original_query_decisions.csv'
    saved = read_rows(manual_path) if manual_path.exists() else []
    if len({r['query_id'] for r in saved}) != len(saved):
        raise ValueError('ID keputusan duplikat.')
    current_ids = {r['query_id'] for r in records}
    by_id = {r['query_id']: r for r in saved}
    if set(by_id) - current_ids:
        raise ValueError('Sumber keputusan lama hilang; arsipkan dan selaraskan sebelum melanjutkan.')
    for query_id, change in (decisions or {}).items():
        if query_id not in current_ids:
            raise ValueError(f'ID tidak ditemukan: {query_id}')
        by_id[query_id] = {'query_id': query_id, **change}
    for row in records:
        decision = by_id.get(row['query_id'])
        if decision:
            if set(decision) != set(DECISION_FIELDS) or decision['status'] not in {'pending', 'accepted', 'needs_review', 'excluded'}:
                raise ValueError('Keputusan harus memiliki query_id, status, reason yang valid.')
            if decision['status'] != 'pending' and not decision['reason'].strip():
                raise ValueError('Alasan keputusan wajib diisi.')
            if decision['status'] == 'accepted' and row['language_eligibility'] != 'eligible':
                raise ValueError('Sumber non-Indonesia belum boleh diterima pada protokol ini.')
            if row['language_eligibility'] == 'eligible':
                row['selection_status'] = decision['status']
                row['selection_reason'] = decision['reason']
    output = ROOT / 'data/interim/original_queries'
    write_csv(output / 'source_pool.csv', records, FIELDS)
    candidates = [r for r in records if r['language_eligibility'] == 'eligible']
    write_csv(output / 'candidates_id.csv', candidates, FIELDS)
    write_csv(output / 'deferred_language.csv', [r for r in records if r['language_eligibility'] != 'eligible'], FIELDS)
    accepted = [r for r in records if r['selection_status'] == 'accepted']
    write_csv(output / 'accepted.csv', accepted, FIELDS)
    # All source occurrences remain in source_pool; final query list is unique by query_id.
    unique_accepted = list({r['query_id']: r for r in accepted}.values())
    write_csv(output / 'accepted_unique.csv', unique_accepted, FIELDS)
    write_csv(manual_path, list(by_id.values()), DECISION_FIELDS)
    print('Kemunculan sumber:', len(records))
    print('Kandidat Indonesia:', len(candidates), dict(Counter(r['domain'] for r in candidates)))
    print('Ditunda karena bahasa:', len(records)-len(candidates))
    print('Query unik diterima:', len(unique_accepted))
    return records


if __name__ == '__main__':
    prepare()
