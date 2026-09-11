"""Pengumpulan utama Google organik + Gemini B; resume dan ekspor pasangan kandidat."""

import argparse
import csv
import json
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from collect_paa import fetch, quota, sanitize, digest, now, read_json, write_json, write_csv
from pilot_gemini_grounding import generate, GenerationError, load_key, resolve_url, grounding, destination_url

ROOT = Path(__file__).resolve().parents[1]
PAIR_FIELDS = ['pair_id', 'query_id', 'query_text', 'domain', 'article_id', 'article_url',
               'google_positions', 'google_title', 'google_snippet', 'n_scheduled', 'n_valid',
               'n_cited', 'n_unknown_matches', 'citation_proportion', 'citation_lower', 'citation_upper',
               'citation_label', 'label_status', 'grounding_eligible', 'collection_complete',
               'collection_gap_hours', 'within_time_window', 'article_status', 'ready_for_model']
UNION_PAIR_FIELDS = PAIR_FIELDS + ['article_title', 'candidate_origin', 'in_google_top10',
                                 'in_gemini_citations']
QUERY_FIELDS = ['query_id', 'query_text', 'domain', 'google_status', 'n_google_results', 'n_trial_records',
                'n_valid', 'grounding_eligible', 'collection_complete', 'collection_gap_hours', 'within_time_window']
TRIAL_FIELDS = ['query_id', 'trial_id', 'repetition', 'status', 'valid_grounding', 'finish_reason',
                'model_version', 'n_web_sources', 'n_cited_sources', 'n_search_queries', 'started_at',
                'prompt_tokens', 'output_tokens', 'thought_tokens', 'total_tokens', 'error']
SOURCE_FIELDS = ['query_id', 'trial_id', 'chunk_index', 'is_cited', 'title', 'source_url', 'raw_url', 'resolution_status']
GOOGLE_FIELDS = ['query_id', 'position', 'title', 'snippet', 'raw_url', 'source_url', 'normalized_url', 'resolution_status']


def read_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def get_serp_key(variable):
    value = os.environ.get(variable, '').strip()
    if not value and (ROOT / '.env').exists():
        for line in (ROOT / '.env').read_text(encoding='utf-8-sig').splitlines():
            name, sep, candidate = line.partition('=')
            if sep and name.strip() == variable:
                value = candidate.strip().strip('\"\'')
                break
    if not value:
        raise ValueError(f'Isi {variable} pada environment atau .env; jangan kirim key ke chat.')
    return value


def normalize_url(url):
    """Conservative: do not merge www, HTTP/HTTPS, path case, AMP, or trailing slash."""
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except (TypeError, ValueError):
        return ''
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
        return ''
    host = parsed.hostname.lower()
    if ':' in host:
        host = '[' + host + ']'
    if port and not ((parsed.scheme == 'http' and port == 80) or (parsed.scheme == 'https' and port == 443)):
        host += ':' + str(port)
    # Preserve raw query encoding/order; only remove explicit tracking parameters.
    tracking = {'fbclid', 'gclid', 'dclid', 'msclkid'}
    query_parts = [part for part in parsed.query.split('&') if part and
                   not part.split('=', 1)[0].lower().startswith('utm_') and
                   part.split('=', 1)[0].lower() not in tracking]
    return urlunsplit((parsed.scheme, host, parsed.path or '/', '&'.join(query_parts), ''))


def make_manifest(config):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', config['dataset_id']):
        raise ValueError('dataset_id tidak valid.')
    if not re.fullmatch(r'[A-Za-z0-9._-]+', config['model']):
        raise ValueError('ID model tidak valid.')
    for field in ['repetitions', 'min_valid_trials', 'max_serp_searches']:
        if type(config[field]) is not int or config[field] < 1:
            raise ValueError(f'{field} harus bilangan positif.')
    if config['min_valid_trials'] > config['repetitions']:
        raise ValueError('Minimal valid melebihi jumlah percobaan.')
    if type(config['serp_quota_reserve']) is not int or config['serp_quota_reserve'] < 0:
        raise ValueError('Cadangan kuota harus bilangan bulat nonnegatif.')
    threshold = config['citation_threshold']
    if threshold is not None and not 0 < threshold <= 1:
        raise ValueError('Ambang label harus di antara 0 (eksklusif) dan 1.')
    if config['generation_config'].get('candidateCount') != 1:
        raise ValueError('Gunakan satu kandidat per percobaan.')
    if config['max_collection_gap_hours'] <= 0 or config['normalization_version'] != 'conservative_v1':
        raise ValueError('Jendela waktu/versi normalisasi tidak valid.')
    if config['google_parameters'].get('engine') != 'google' or set(config['google_parameters']) - {
        'engine', 'google_domain', 'gl', 'hl', 'location', 'device'
    }:
        raise ValueError('Gunakan Google organik dengan parameter lokasi/bahasa yang didukung.')
    path = (ROOT / config['query_csv']).resolve()
    path.relative_to(ROOT)
    rows = read_rows(path)
    if not rows or len(rows) > config['max_serp_searches']:
        raise ValueError('Query diterima kosong atau melebihi anggaran batch.')
    if len({r['query_id'] for r in rows}) != len(rows):
        raise ValueError('query_id duplikat.')
    for row in rows:
        if row['selection_status'] != 'accepted' or row['language'] != 'id':
            raise ValueError('Hanya query asli Indonesia yang diterima boleh dikumpulkan.')
    # Interleave domains instead of exhausting one domain before another.
    buckets = {d: [r for r in rows if r['domain'] == d] for d in sorted({r['domain'] for r in rows})}
    ordered = [bucket[i] for i in range(max(map(len, buckets.values()))) for bucket in buckets.values() if i < len(bucket)]
    return {'config': config, 'queries': ordered, 'pipeline_version': 1}


def trial_info(trial):
    candidate, meta, web, cited, text = grounding(trial.get('response', {}))
    valid = trial.get('status') == 'completed' and candidate.get('finishReason') == 'STOP' and bool(text) and bool(cited)
    return bool(valid), candidate, meta, web, cited


def organic_rows(google):
    items = google.get('response', {}).get('organic_results') or []
    if not isinstance(items, list):
        return []
    # Do not substitute ads, PAA, videos block, or sitelinks for missing organic results.
    selected = {}
    for row in items:
        if isinstance(row, dict) and type(row.get('position')) is int and 1 <= row['position'] <= 10 and row.get('link'):
            selected.setdefault(row['position'], row)
    return [selected[position] for position in sorted(selected)]


def export_dataset(manifest, data_root):
    config = manifest['config']
    raw = data_root / 'raw/main' / config['dataset_id'] / 'queries'
    pairs, union_pairs, queries, trials, sources, results = [], [], [], [], [], []
    for query in manifest['queries']:
        qid = query['query_id']
        path = raw / (qid + '.json')
        record = read_json(path) if path.exists() else {}
        google = record.get('google', {})
        g_rows = organic_rows(google)
        experiments = record.get('trials', [])
        valid = [t for t in experiments if trial_info(t)[0]]
        complete = google.get('status') == 'completed' and len(experiments) == config['repetitions'] and all(t.get('status') in {'completed', 'error'} for t in experiments)
        times = [google.get('started_at')] + [t.get('started_at') for t in experiments]
        times = [datetime.fromisoformat(t) for t in times if t]
        gap = (max(times)-min(times)).total_seconds()/3600 if times else None
        close = gap is not None and gap <= config['max_collection_gap_hours']
        eligible = len(valid) >= config['min_valid_trials']
        queries.append(dict(zip(QUERY_FIELDS, [qid, query['query_text'], query['domain'], google.get('status', 'not_requested'), len(g_rows), len(experiments), len(valid), eligible, complete, gap if gap is not None else '', close])))
        cited_sets = []
        cited_titles = {}
        for trial in experiments:
            is_valid, candidate, meta, web, cited = trial_info(trial)
            payload = trial.get('response', {})
            usage = payload.get('usageMetadata') or {}
            trials.append(dict(zip(TRIAL_FIELDS, [qid, trial['trial_id'], trial['repetition'], trial['status'], is_valid, candidate.get('finishReason', ''), payload.get('modelVersion', ''), len(web), len(cited), len(meta.get('webSearchQueries') or []), trial['started_at'], usage.get('promptTokenCount', ''), usage.get('candidatesTokenCount', ''), usage.get('thoughtsTokenCount', ''), usage.get('totalTokenCount', ''), trial.get('error', '')])))
            cited_urls = set()
            unknown = False
            for index, source in web.items():
                resolution = trial.get('url_resolutions', {}).get(source['uri'], {})
                final = destination_url(resolution)
                sources.append(dict(zip(SOURCE_FIELDS, [qid, trial['trial_id'], index, index in cited, source.get('title', ''), final, source['uri'], resolution.get('resolution_status', '')])))
                if index in cited:
                    normalized = normalize_url(final) if final else ''
                    if normalized:
                        cited_urls.add(normalized)
                        if is_valid:
                            cited_titles.setdefault(normalized, source.get('title', ''))
                    else:
                        unknown = True
            if is_valid:
                cited_sets.append((cited_urls, unknown))
        articles = {}
        for item in g_rows:
            resolution = google.get('url_resolutions', {}).get(item['link'], {})
            final = destination_url(resolution)
            normalized = normalize_url(final or item['link'])
            if not normalized:
                continue
            results.append(dict(zip(GOOGLE_FIELDS, [qid, item['position'], item.get('title', ''), item.get('snippet', ''), item['link'], final, normalized, resolution.get('resolution_status', '')])))
            article = articles.setdefault(normalized, {'positions': [], 'item': item, 'final': final,
                                                       'in_google': True, 'title': item.get('title', '')})
            article['positions'].append(item['position'])
        # Additional cited sources form a separate candidate view. Keep all trial sources
        # (including invalid trials and unresolved redirects) in sources.csv for audit.
        for url, title in sorted(cited_titles.items()):
            articles.setdefault(url, {'positions': [], 'item': {}, 'final': url,
                                      'in_google': False, 'title': title})
        for url, article in articles.items():
            n_cited = sum(url in urls for urls, unknown in cited_sets)
            n_unknown = sum(url not in urls and (unknown or not article['final']) for urls, unknown in cited_sets)
            lower = n_cited / len(valid) if valid else ''
            upper = (n_cited+n_unknown) / len(valid) if valid else ''
            proportion = lower if valid and n_unknown == 0 else ''
            label, label_status = '', 'threshold_not_set'
            if not complete or not eligible or not close:
                label_status = 'query_not_eligible_or_incomplete'
            elif n_unknown:
                label_status = 'url_matching_uncertain'
            elif config['citation_threshold'] is not None:
                label = int(proportion >= config['citation_threshold'])
                label_status = 'labeled_candidate'
            article_id = 'article_' + digest(url)
            item = article['item']
            pair = dict(zip(PAIR_FIELDS, ['pair_' + digest(qid + article_id), qid, query['query_text'], query['domain'], article_id, url, json.dumps(sorted(article['positions'])), item.get('title', ''), item.get('snippet', ''), config['repetitions'], len(valid), n_cited, n_unknown, proportion, lower, upper, label, label_status, eligible, complete, gap if gap is not None else '', close, 'pending_crawl_and_article_review', False]))
            if article['in_google']:
                pairs.append(pair)
            origin = ('google_and_gemini' if n_cited else 'google_only') if article['in_google'] else 'gemini_only'
            union_pairs.append({**pair, 'article_title': article['title'], 'candidate_origin': origin,
                                'in_google_top10': article['in_google'], 'in_gemini_citations': n_cited > 0})
    output = data_root / 'interim/main' / config['dataset_id']
    for name, rows, fields in [('queries', queries, QUERY_FIELDS), ('trials', trials, TRIAL_FIELDS), ('sources', sources, SOURCE_FIELDS), ('google_results', results, GOOGLE_FIELDS), ('query_article_pairs', pairs, PAIR_FIELDS), ('query_article_pairs_union', union_pairs, UNION_PAIR_FIELDS)]:
        write_csv(output / (name + '.csv'), rows, fields)
    write_json(output / 'candidate_pool_protocol.json', {
        'version': 'google_top10_plus_valid_citations_v1', 'exported_at': now(),
        'collection_manifest_digest': digest(json.dumps(manifest, ensure_ascii=False, sort_keys=True)),
        'inclusion': 'Union of saved Google organic positions 1-10 and resolved web sources cited in valid Gemini trials.',
        'trial_policy': config['valid_trial_definition'], 'minimum_valid_trials': config['min_valid_trials'],
        'citation_threshold': config['citation_threshold'], 'normalization_version': config['normalization_version'],
        'unresolved_sources': 'Preserved in sources.csv; no invented article URL or negative match.',
        'audit_columns_not_predictors': ['candidate_origin', 'in_gemini_citations', 'n_cited',
                                        'n_unknown_matches', 'citation_proportion', 'citation_lower', 'citation_upper'],
        'sampling_note': 'Candidate inclusion partly depends on observed citations. Google rank/presence/missingness can reveal selection; do not use them in union-view prediction without revising and validating the sampling design.',
    })
    print('Ekspor:', len(queries), 'query terjadwal;', len(trials), 'percobaan;', len(pairs),
          'pasangan Google;', len(union_pairs), 'pasangan gabungan.')
    return pairs


def collect(manifest, data_root, serp_key, gemini_key, max_queries=None, fetcher=fetch, generator=generate, resolver=resolve_url, quota_reader=quota):
    config = manifest['config']
    raw = data_root / 'raw/main' / config['dataset_id']
    raw.mkdir(parents=True, exist_ok=True)
    lock = raw / 'running.lock'
    with lock.open('x') as handle:
        handle.write(str(os.getpid()))
    try:
        frozen = raw / 'manifest.json'
        if frozen.exists() and read_json(frozen) != manifest:
            raise ValueError('Batch berubah. Gunakan dataset_id baru; jangan mengubah protokol di tengah batch.')
        jobs = []
        for query in manifest['queries']:
            path = raw / 'queries' / (query['query_id'] + '.json')
            saved = read_json(path) if path.exists() else {}
            if saved.get('status') != 'completed':
                jobs.append(query)
        jobs = jobs[:max_queries] if max_queries is not None else jobs
        needed = sum(not (raw / 'queries' / (q['query_id'] + '.json')).exists() for q in jobs)
        if needed:
            account = quota_reader(serp_key)
            if account['total_searches_left'] < needed + config['serp_quota_reserve']:
                raise RuntimeError(f"Sisa kuota {account['total_searches_left']} tidak cukup untuk {needed} pencarian dan cadangan {config['serp_quota_reserve']}.")
            write_json(raw / ('quota_before_' + digest(now()) + '.json'), account)
        write_json(frozen, manifest)
        for query in jobs:
            qid = query['query_id']
            path = raw / 'queries' / (qid + '.json')
            record = read_json(path) if path.exists() else {'query': query, 'status': 'started', 'google': {'status': 'started', 'started_at': now()}, 'trials': []}
            if not path.exists():
                write_json(path, record)
                try:
                    payload = sanitize(fetcher('search.json', {**config['google_parameters'], 'q': query['query_text']}, serp_key), serp_key)
                    record['google']['response'] = payload
                    if payload.get('error') or payload.get('search_metadata', {}).get('status') != 'Success':
                        raise RuntimeError('Google Search tidak berhasil.')
                    record['google']['status'] = 'response_saved'
                except RuntimeError as error:
                    record['google']['status'] = 'error'
                    record['google']['error_code'] = getattr(error, 'code', 'search_error')
                    record['google']['error_details'] = getattr(error, 'details', {})
                    write_json(path, record)
                    export_dataset(manifest, data_root)
                    raise
                write_json(path, record)
            google = record['google']
            if google['status'] in {'started', 'error'}:
                raise RuntimeError('Checkpoint Google gagal/tidak pasti. Periksa sebelum mengulang; tidak ada retry API otomatis.')
            if google['status'] == 'response_saved':
                # Checkpoint must contain the complete query record, not only its Google section.
                resolutions = google.setdefault('url_resolutions', {})
                for url in dict.fromkeys(r['link'] for r in organic_rows(google)):
                    if url not in resolutions:
                        resolutions[url] = resolver(url)
                        write_json(path, record)
                google['status'] = 'completed'
                write_json(path, record)
            for repetition in range(1, config['repetitions'] + 1):
                trial = next((t for t in record['trials'] if t['repetition'] == repetition), None)
                if trial is None:
                    trial = {'trial_id': 'main_trial_' + digest(config['dataset_id'] + qid + str(repetition)), 'repetition': repetition, 'status': 'started', 'started_at': now()}
                    record['trials'].append(trial)
                    write_json(path, record)
                    request = {'contents': [{'role': 'user', 'parts': [{'text': query['query_text']}]}],
                               'tools': [{'google_search': {}}],
                               'systemInstruction': {'parts': [{'text': config['system_instruction']}]},
                               'generationConfig': config['generation_config']}
                    try:
                        trial['response'] = generator(config['model'], request, gemini_key)
                    except GenerationError as error:
                        trial.update(status='error', error=error.code)
                        if error.details:
                            trial['error_details'] = error.details
                        if len(record['trials']) == config['repetitions'] and all(
                            t['status'] in {'completed', 'error'} for t in record['trials']
                        ):
                            record['status'] = 'completed'
                        write_json(path, record)
                        export_dataset(manifest, data_root)
                        raise
                    trial['status'] = 'response_saved'
                    write_json(path, record)
                if trial['status'] == 'started':
                    raise RuntimeError('Percobaan Gemini terputus dengan hasil tidak pasti; tidak diulang otomatis.')
                if trial['status'] == 'response_saved':
                    _, _, web, _, _ = grounding(trial['response'])
                    resolutions = trial.setdefault('url_resolutions', {})
                    for url in dict.fromkeys(r['uri'] for r in web.values()):
                        if url not in resolutions:
                            resolutions[url] = resolver(url)
                            write_json(path, record)
                    trial['status'] = 'completed'
                    trial['completed_at'] = now()
                    write_json(path, record)
                    print(query['domain'], '|', query['query_text'], '| percobaan', repetition,
                          '| valid:', trial_info(trial)[0], flush=True)
            record['status'] = 'completed'
            write_json(path, record)
            export_dataset(manifest, data_root)
            print(query['domain'], '|', query['query_text'], '| pengumpulan selesai', flush=True)
        return export_dataset(manifest, data_root)
    finally:
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/main_dataset.json')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--run', action='store_true')
    modes.add_argument('--export-only', action='store_true')
    parser.add_argument('--max-queries', type=int, help='Maksimum query yang belum selesai untuk eksekusi ini.')
    args = parser.parse_args()
    if args.max_queries is not None and args.max_queries < 1:
        parser.error('--max-queries harus positif.')
    manifest = make_manifest(read_json(args.config))
    config = manifest['config']
    print('Dataset utama:', config['dataset_id'])
    print('Query:', len(manifest['queries']), dict(Counter(r['domain'] for r in manifest['queries'])))
    print('SerpApi maksimal:', len(manifest['queries']), '| Gemini maksimal:', len(manifest['queries']) * config['repetitions'])
    print('Percobaan per query:', config['repetitions'], '| minimal valid:', config['min_valid_trials'], '| ambang label:', config['citation_threshold'])
    if args.run:
        collect(manifest, ROOT / 'data', get_serp_key(config['serp_api_key_variable']), load_key(), args.max_queries)
    elif args.export_only:
        frozen = ROOT / 'data/raw/main' / config['dataset_id'] / 'manifest.json'
        if frozen.exists() and read_json(frozen) != manifest:
            raise ValueError('Gunakan konfigurasi batch yang sama dengan manifest tersimpan.')
        export_dataset(manifest, ROOT / 'data')
    else:
        print('Pratinjau lokal. Tambahkan --run untuk mengumpulkan batch utama, atau --max-queries 3 untuk membatasi satu eksekusi.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, ValueError, FileExistsError) as error:
        print(str(error))
        raise SystemExit(1)
