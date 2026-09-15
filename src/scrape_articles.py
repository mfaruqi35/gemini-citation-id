"""Collect article pages directly; bounded requests, robots checks and resumable audit.

No SerpApi/Gemini credentials or API calls are used. Preview is read-only by default.
"""

import argparse
import csv
import hashlib
import ipaddress
import json
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

try:
    import requests
except ModuleNotFoundError:
    requests = None

from collect_paa import now, read_json, write_csv, write_json

ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = {
    'dataset_id': 'articles_main_01',
    'source_batches': ['main_01'],
    'timeout_seconds': 25,
    'max_bytes': 5 * 1024 * 1024,
    'per_host_delay_seconds': 1,
    'user_agent': 'CitationResearchBot/1.0 (academic article analysis)',
    'respect_robots': True,
    'min_words': 100,
    'max_redirects': 5,
}
RETRYABLE = {'network_error', 'http_error', 'robots_unavailable', 'robots_disallowed',
             'blocked_or_challenge', 'response_too_large', 'extraction_error', 'interrupted'}
ARTICLE_FIELDS = ['article_id', 'article_url', 'research_domains', 'candidate_origins',
                  'query_ids', 'pair_ids', 'source_batches', 'scrape_status', 'attempt_count',
                  'started_at', 'finished_at', 'http_status', 'final_url', 'robots_status',
                  'error_type', 'raw_html_path', 'extraction_path']


def is_true(value):
    return value is True or str(value).lower() == 'true'


def safe_path(root, value):
    path = (Path(root) / value).resolve()
    path.relative_to(Path(root).resolve())
    if path == Path(root).resolve():
        raise ValueError('Direktori proyek tidak boleh menjadi target output.')
    return path


def normalized_config(config):
    result = {**DEFAULTS, **config}
    if not re.fullmatch(r'[A-Za-z0-9_-]+', result['dataset_id']):
        raise ValueError('dataset_id tidak valid.')
    batches = result['source_batches']
    if not isinstance(batches, list) or not batches or len(set(batches)) != len(batches):
        raise ValueError('source_batches harus daftar batch unik yang tidak kosong.')
    if any(not re.fullmatch(r'[A-Za-z0-9_-]+', batch) for batch in batches):
        raise ValueError('Nama source_batches tidak valid.')
    for key in ('timeout_seconds', 'max_bytes', 'min_words'):
        if not isinstance(result[key], (float, int)) or result[key] <= 0:
            raise ValueError(f'{key} harus positif.')
    for key in ('max_bytes', 'min_words', 'max_redirects'):
        if type(result[key]) is not int or result[key] < 1:
            raise ValueError(f'{key} harus bilangan bulat positif.')
    if not isinstance(result['per_host_delay_seconds'], (int, float)) or result['per_host_delay_seconds'] < 0:
        raise ValueError('per_host_delay_seconds harus nonnegatif.')
    if result['respect_robots'] is not True:
        raise ValueError('Pengumpulan ini mensyaratkan respect_robots=true.')
    if not isinstance(result['user_agent'], str) or not result['user_agent'].strip():
        raise ValueError('Isi user_agent yang mendeskripsikan pengumpulan.')
    result.setdefault('raw_dir', f"data/raw/articles/{result['dataset_id']}")
    result.setdefault('interim_dir', f"data/interim/articles/{result['dataset_id']}")
    return result


def valid_public_url(url):
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in {'https', 'http'} or not parsed.hostname or parsed.username or parsed.password:
            return False
        if parsed.hostname.lower() in {'localhost', 'localhost.localdomain'} or parsed.hostname.endswith('.local'):
            return False
        if parsed.port not in {None, 80, 443}:
            return False
        try:
            return ipaddress.ip_address(parsed.hostname).is_global
        except ValueError:
            return '.' in parsed.hostname
    except (TypeError, ValueError):
        return False


def make_manifest(config, root=ROOT):
    """Freeze all eligible union pairs; URL order balances domain/origin and hosts."""
    config = normalized_config(config)
    safe_path(root, config['raw_dir'])
    safe_path(root, config['interim_dir'])
    pairs, fingerprints, by_url, id_urls = [], {}, {}, {}
    for batch in config['source_batches']:
        path = safe_path(root, f'data/interim/main/{batch}/query_article_pairs_union.csv')
        fingerprints[batch] = hashlib.sha256(path.read_bytes()).hexdigest()
        with path.open(encoding='utf-8-sig', newline='') as handle:
            for source in csv.DictReader(handle):
                if not (is_true(source['grounding_eligible']) and is_true(source['within_time_window'])
                        and is_true(source['collection_complete'])):
                    continue
                row = {**source, 'source_batch': batch}
                pairs.append(row)
                url = row['article_url']
                article_id = row['article_id'] or 'article_' + hashlib.sha256(url.encode()).hexdigest()[:24]
                if not re.fullmatch(r'article_[A-Za-z0-9_-]+', article_id):
                    raise ValueError('article_id tidak aman untuk nama checkpoint.')
                if article_id in id_urls and id_urls[article_id] != url:
                    raise ValueError('article_id yang sama mengacu ke URL berbeda.')
                id_urls[article_id] = url
                if url not in by_url:
                    by_url[url] = {'article_id': article_id, 'article_url': url,
                                   'research_domains': [], 'candidate_origins': [],
                                   'query_ids': [], 'pair_ids': [], 'source_batches': []}
                article = by_url[url]
                if article['article_id'] != article_id:
                    raise ValueError('URL yang sama memiliki article_id berbeda antarbatch.')
                for field, value in [('research_domains', row['domain']),
                                     ('candidate_origins', row['candidate_origin']),
                                     ('query_ids', row['query_id']), ('pair_ids', row['pair_id']),
                                     ('source_batches', batch)]:
                    if value not in article[field]:
                        article[field].append(value)
    if not pairs:
        raise ValueError('Tidak ada pasangan union dengan pengumpulan lengkap dan query eligible.')
    buckets = defaultdict(list)
    for article in by_url.values():
        origins = set(article['candidate_origins'])
        origin = ('google_and_gemini' if 'google_and_gemini' in origins or 'both' in origins
                  or {'google_only', 'gemini_only'} <= origins else sorted(origins)[0])
        buckets[(article['research_domains'][0], origin)].append(article)
    hosts, queries, articles = Counter(), Counter(), []
    while any(buckets.values()):
        for bucket_key in sorted(buckets):
            bucket = buckets[bucket_key]
            if not bucket:
                continue
            index = min(range(len(bucket)), key=lambda i: (
                hosts[urlsplit(bucket[i]['article_url']).hostname],
                min(queries[q] for q in bucket[i]['query_ids']), i))
            article = bucket.pop(index)
            articles.append(article)
            hosts[urlsplit(article['article_url']).hostname] += 1
            queries.update(article['query_ids'])
    return {'pipeline_version': 1, 'config': config, 'source_fingerprints': fingerprints,
            'articles': articles, 'pairs': pairs}


def paths(manifest, root=ROOT):
    return (safe_path(root, manifest['config']['raw_dir']),
            safe_path(root, manifest['config']['interim_dir']))


def load_record(raw, article):
    path = raw / 'records' / (article['article_id'] + '.json')
    return read_json(path) if path.exists() else {
        'article_id': article['article_id'], 'article_url': article['article_url'],
        'status': 'not_requested', 'attempts': [], 'extraction': {}}


def pending_articles(manifest, root=ROOT, retry_failed=False):
    raw, _ = paths(manifest, root)
    rows = []
    for article in manifest['articles']:
        record = load_record(raw, article)
        if ((not retry_failed and record['status'] == 'not_requested')
                or (retry_failed and record['status'] in RETRYABLE)):
            rows.append(article)
    return rows


class DirectFetcher:
    """Small HTTP client: manual redirects preserve robots checks on every host."""

    def __init__(self, config, session=None, sleeper=time.sleep, clock=time.monotonic):
        if requests is None:
            raise RuntimeError('Pasang requirements-articles.txt sebelum --run; preview tidak memerlukan requests.')
        self.config = normalized_config(config)
        self.session = session or requests.Session()
        self.session.headers.update({'User-Agent': self.config['user_agent'],
                                     'Accept': 'text/html,application/xhtml+xml,text/plain;q=0.8'})
        self.sleeper, self.clock = sleeper, clock
        self.last_request, self.robots_cache = {}, {}

    def close(self):
        self.session.close()

    def _request(self, url, max_bytes):
        if not valid_public_url(url):
            return {'status': 'invalid_url', 'error_type': 'non_public_or_unsupported_url',
                    'final_url': url, 'body': b'', 'headers': {}}
        host = urlsplit(url).netloc
        elapsed = self.clock() - self.last_request.get(host, float('-inf'))
        remaining = self.config['per_host_delay_seconds'] - elapsed
        if remaining > 0:
            self.sleeper(remaining)
        self.last_request[host] = self.clock()
        try:
            with self.session.get(url, timeout=(min(10, self.config['timeout_seconds']),
                                              self.config['timeout_seconds']),
                                  allow_redirects=False, stream=True) as response:
                result = {'status': 'received', 'http_status': response.status_code,
                          'final_url': url, 'headers': dict(response.headers), 'body': b''}
                chunks, size = [], 0
                for chunk in response.iter_content(chunk_size=65536):
                    if not chunk:
                        continue
                    size += len(chunk)
                    if size > max_bytes:
                        result['status'] = 'response_too_large'
                        result['error_type'] = 'max_bytes_exceeded'
                        result['body'] = b''.join(chunks)
                        return result
                    chunks.append(chunk)
                result['body'] = b''.join(chunks)
                return result
        except requests.RequestException as exc:
            # Exception text can contain tokens from publisher URLs; retain type only.
            return {'status': 'network_error', 'error_type': type(exc).__name__,
                    'final_url': url, 'headers': {}, 'body': b''}

    def _robot_rules(self, url):
        parsed = urlsplit(url)
        origin = f'{parsed.scheme}://{parsed.netloc}'
        if origin in self.robots_cache:
            return self.robots_cache[origin]
        robot_url = origin + '/robots.txt'
        history = []
        for _ in range(self.config['max_redirects'] + 1):
            result = self._request(robot_url, 512 * 1024)
            history.append({'url': robot_url, 'http_status': result.get('http_status'),
                            'status': result['status']})
            location = next((v for k, v in result['headers'].items() if k.lower() == 'location'), '')
            if result['status'] == 'received' and result.get('http_status') in {301, 302, 303, 307, 308} and location:
                robot_url = urljoin(robot_url, location)
                continue
            break
        else:
            result['status'] = 'too_many_redirects'
        status = result.get('http_status')
        parser, body = None, ''
        if result['status'] != 'received':
            state = 'unavailable'
        elif status in {404, 410}:
            state = 'not_found_allow'
        elif status in {401, 403}:
            state = 'forbidden'
        elif status == 200:
            body = result['body'].decode('utf-8-sig', errors='replace')
            if re.search(r'<(?:html|!doctype)', body[:500], re.I):
                state = 'unavailable'
            else:
                parser = RobotFileParser()
                parser.set_url(origin + '/robots.txt')
                parser.parse(body.splitlines())
                state = 'parsed'
        else:
            state = 'unavailable'
        value = {'status': state, 'parser': parser, 'checked_at': now(),
                 'robots_url': origin + '/robots.txt', 'http_status': status,
                 'history': history, 'robots_text': body,
                 'user_agent': self.config['user_agent']}
        self.robots_cache[origin] = value
        return value

    def robots_check(self, url):
        if not valid_public_url(url):
            return {'status': 'invalid_url', 'allowed': False}
        rules = self._robot_rules(url)
        result = {k: v for k, v in rules.items() if k != 'parser'}
        result['allowed'] = rules['status'] == 'not_found_allow'
        if rules['parser'] is not None:
            agent = self.config['user_agent'].split()[0]
            result['allowed'] = rules['parser'].can_fetch(agent, url)
            delay = rules['parser'].crawl_delay(agent)
            rate = rules['parser'].request_rate(agent)
            if rate and rate.requests:
                delay = max(delay or 0, rate.seconds / rate.requests)
            result['crawl_delay_seconds'] = delay
        return result

    def fetch(self, url):
        history, checks = [], []
        current = url
        for _ in range(self.config['max_redirects'] + 1):
            check = self.robots_check(current)
            checks.append({'page_url': current, **check})
            if not check['allowed']:
                status = 'robots_unavailable' if check['status'] == 'unavailable' else 'robots_disallowed'
                if check['status'] == 'invalid_url':
                    status = 'invalid_url'
                return {'status': status, 'final_url': current, 'body': b'',
                        'robots_status': check['status'], 'robots_checks': checks,
                        'redirect_history': history, 'error_type': status}
            if check.get('crawl_delay_seconds'):
                host = urlsplit(current).netloc
                wait = check['crawl_delay_seconds'] - (self.clock() - self.last_request.get(host, float('-inf')))
                if wait > 0:
                    self.sleeper(wait)
            result = self._request(current, self.config['max_bytes'])
            result.update({'robots_status': check['status'], 'robots_checks': checks,
                           'redirect_history': history})
            code = result.get('http_status')
            location = next((v for k, v in result.get('headers', {}).items() if k.lower() == 'location'), '')
            if result['status'] == 'received' and code in {301, 302, 303, 307, 308} and location:
                history.append({'url': current, 'http_status': code, 'location': location})
                current = urljoin(current, location)
                continue
            if result['status'] != 'received':
                return result
            if code < 200 or code >= 300:
                result['status'] = 'http_error'
                result['error_type'] = 'HTTP_' + str(code)
                return result
            content_type = next((v for k, v in result['headers'].items() if k.lower() == 'content-type'), '')
            result['content_type'] = content_type
            if not ('text/html' in content_type.lower() or 'application/xhtml+xml' in content_type.lower()):
                result['status'] = 'non_html'
                result['error_type'] = 'unsupported_content_type'
                return result
            html = decode_body(result['body'], content_type)
            if is_challenge(html):
                result['status'] = 'blocked_or_challenge'
                result['error_type'] = 'challenge_page_detected'
            else:
                result['status'] = 'success'
            return result
        return {'status': 'http_error', 'final_url': current, 'body': b'',
                'error_type': 'too_many_redirects', 'robots_checks': checks,
                'redirect_history': history}


def decode_body(body, content_type=''):
    match = re.search(r'charset\s*=\s*["\']?([^;\s"\'>]+)', content_type, re.I)
    if not match:
        match = re.search(r'charset\s*=\s*["\']?([^;\s"\'>]+)', body[:2048].decode('ascii', errors='ignore'), re.I)
    encoding = match.group(1) if match else 'utf-8'
    try:
        return body.decode(encoding, errors='replace')
    except LookupError:
        return body.decode('utf-8', errors='replace')


def is_challenge(html):
    head = html[:20000].lower()
    title_match = re.search(r'<title[^>]*>(.*?)</title>', head, re.S)
    title = title_match.group(1) if title_match else ''
    title_flags = ('just a moment', 'access denied', 'attention required', 'verify you are human',
                   'checking your browser', 'security verification')
    return any(flag in title for flag in title_flags) or 'cf-chl-' in head or '__cf_chl_' in head


def export_articles(manifest, root=ROOT):
    raw, interim = paths(manifest, root)
    rows, extra_fields = [], set()
    for article in manifest['articles']:
        record = load_record(raw, article)
        latest = record['attempts'][-1] if record['attempts'] else {}
        row = {k: json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v for k, v in article.items()}
        row.update({key: latest.get(key, '') for key in ARTICLE_FIELDS if key not in row})
        row['scrape_status'] = record['status']
        row['attempt_count'] = len(record['attempts'])
        for key, value in record.get('extraction', {}).items():
            if key not in ARTICLE_FIELDS and (value is None or isinstance(value, (str, int, float, bool))):
                row[key] = value
                extra_fields.add(key)
        rows.append(row)
    write_csv(interim / 'articles.csv', rows, ARTICLE_FIELDS + sorted(extra_fields))
    pair_fields = list(manifest['pairs'][0])
    write_csv(interim / 'source_pairs.csv', manifest['pairs'], pair_fields)
    summary = {'dataset_id': manifest['config']['dataset_id'], 'exported_at': now(),
               'n_unique_urls': len(rows), 'n_source_pairs': len(manifest['pairs']),
               'scrape_status': dict(Counter(row['scrape_status'] for row in rows))}
    write_json(interim / 'scrape_summary.json', summary)
    return rows


def collect(manifest, root=ROOT, max_new_urls=20, retry_failed=False, fetcher=None, extractor=None):
    if type(max_new_urls) is not int or max_new_urls < 1:
        raise ValueError('max_new_urls harus bilangan bulat positif.')
    if extractor is None:
        from article_features import extract_features
        extractor = extract_features
    raw, _ = paths(manifest, root)
    raw.mkdir(parents=True, exist_ok=True)
    frozen_path, lock_path = raw / 'manifest.json', raw / 'running.lock'
    if frozen_path.exists() and read_json(frozen_path) != manifest:
        raise ValueError('Manifest berubah. Gunakan dataset_id baru untuk sumber/konfigurasi berbeda.')
    try:
        lock = lock_path.open('x', encoding='utf-8')
    except FileExistsError:
        raise RuntimeError('Pengumpulan terkunci. Pastikan proses lama berhenti sebelum menghapus running.lock.') from None
    client = None
    with lock:
        lock.write(now())
        lock.flush()
        try:
            if not frozen_path.exists():
                write_json(frozen_path, manifest)
            selected = pending_articles(manifest, root, retry_failed)[:max_new_urls]
            if fetcher is None:
                client = DirectFetcher(manifest['config'])
                fetcher = client.fetch
            for index, article in enumerate(selected, 1):
                record = load_record(raw, article)
                attempt_number = len(record['attempts']) + 1
                attempt = {'attempt_number': attempt_number, 'started_at': now(), 'status': 'interrupted'}
                record['attempts'].append(attempt)
                record.update(status='interrupted', extraction={})
                record_path = raw / 'records' / (article['article_id'] + '.json')
                write_json(record_path, record)
                try:
                    result = fetcher(article['article_url'])
                    body = result.pop('body', b'')
                    headers = result.pop('headers', {})
                    attempt.update(result)
                    content_type = attempt.get('content_type') or next(
                        (v for k, v in headers.items() if k.lower() == 'content-type'), '')
                    attempt['content_type'] = content_type
                    attempt['downloaded_bytes'] = len(body)
                    if body:
                        html_path = raw / 'html' / (article['article_id'] + f'_attempt_{attempt_number}.html')
                        html_path.parent.mkdir(parents=True, exist_ok=True)
                        # Preserve downloaded bytes, including HTTP error/challenge pages.
                        html_path.write_bytes(body)
                        attempt['raw_html_path'] = str(html_path.relative_to(Path(root).resolve())).replace('\\', '/')
                        attempt['body_sha256'] = hashlib.sha256(body).hexdigest()
                    if result['status'] == 'success':
                        try:
                            features = extractor(decode_body(body, content_type), result['final_url'],
                                                 min_words=manifest['config']['min_words'])
                            extraction_path = raw / 'extractions' / (article['article_id'] + f'_attempt_{attempt_number}.json')
                            write_json(extraction_path, features)
                            attempt['extraction_path'] = str(extraction_path.relative_to(Path(root).resolve())).replace('\\', '/')
                            record['extraction'] = features
                        except Exception as exc:
                            attempt['status'] = 'extraction_error'
                            attempt['error_type'] = type(exc).__name__
                    attempt['finished_at'] = now()
                    record['status'] = attempt['status']
                    write_json(record_path, record)
                except KeyboardInterrupt:
                    attempt['finished_at'] = now()
                    write_json(record_path, record)
                    raise
                finally:
                    export_articles(manifest, root)
                print(f"{index}/{len(selected)} | {record['status']} | {article['article_url']}", flush=True)
            return export_articles(manifest, root)
        finally:
            if client is not None:
                client.close()
            lock.close()
            lock_path.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', default='configs/article_dataset.json')
    parser.add_argument('--run', action='store_true', help='Aktifkan permintaan langsung ke website.')
    parser.add_argument('--max-new-urls', type=int, default=20)
    parser.add_argument('--retry-failed', action='store_true', help='Izinkan percobaan baru untuk status gagal; riwayat dipertahankan.')
    args = parser.parse_args()
    if args.max_new_urls < 1:
        parser.error('--max-new-urls minimal 1.')
    manifest = make_manifest(read_json(safe_path(ROOT, args.config)))
    raw, _ = paths(manifest)
    if (raw / 'manifest.json').exists() and read_json(raw / 'manifest.json') != manifest:
        raise ValueError('Manifest berbeda. Pertahankan konfigurasi atau buat dataset_id baru.')
    pending = pending_articles(manifest, retry_failed=args.retry_failed)
    print(f"URL unik: {len(manifest['articles'])} | pasangan eligible: {len(manifest['pairs'])}")
    print(f"Belum diambil/diizinkan ulang: {len(pending)} | batas kali ini: {args.max_new_urls}")
    for article in pending[:args.max_new_urls]:
        print(' | '.join([','.join(article['research_domains']), ','.join(article['candidate_origins']), article['article_url']]))
    if not args.run:
        print('Preview saja: tidak ada permintaan jaringan atau perubahan data. Tambahkan --run untuk mengambil halaman.')
        return
    rows = collect(manifest, max_new_urls=args.max_new_urls, retry_failed=args.retry_failed)
    print('Status:', dict(Counter(row['scrape_status'] for row in rows)))


if __name__ == '__main__':
    main()
