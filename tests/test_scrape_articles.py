"""Scraping contract tests: fake HTTP only, no publisher/API calls."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import scrape_articles as scraper
from collect_paa import read_json, write_csv, write_json


def source_pair(index, domain='kesehatan', origin='google_only', url=None, **overrides):
    row = {'pair_id': f'pair_{index}', 'query_id': f'query_{index}',
           'query_text': f'Pertanyaan {index}?', 'domain': domain,
           'article_id': f'article_{index}', 'article_url': url or f'https://site{index}.example/article',
           'candidate_origin': origin, 'grounding_eligible': True,
           'within_time_window': True, 'collection_complete': True}
    return {**row, **overrides}


def fake_extract(html, url, min_words=100):
    return {'title': 'Artikel', 'text': 'Teks artikel dari halaman yang diambil.',
            'n_words': 150, 'article_eligible': True, 'article_review_status': 'eligible_auto',
            'headings': [{'level': 1, 'text': 'Judul'}]}


class ManifestAndResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.config = {'dataset_id': 'test_articles', 'source_batches': ['test_main'],
                       'per_host_delay_seconds': 0}
        self.rows = [source_pair(1), source_pair(2, 'keuangan'), source_pair(3, 'teknologi')]
        self.source = self.root / 'data/interim/main/test_main/query_article_pairs_union.csv'
        self.save_source()

    def tearDown(self):
        self.temp.cleanup()

    def save_source(self):
        write_csv(self.source, self.rows, list(self.rows[0]))

    def manifest(self):
        return scraper.make_manifest(self.config, self.root)

    def test_only_eligible_complete_pairs_but_preserves_shared_url_provenance(self):
        self.rows += [source_pair(4, grounding_eligible=False),
                      source_pair(5, within_time_window=False),
                      source_pair(6, collection_complete=False),
                      source_pair(7, url=self.rows[0]['article_url'], article_id='article_1')]
        self.save_source()
        manifest = self.manifest()
        self.assertEqual(len(manifest['articles']), 3)
        self.assertEqual(len(manifest['pairs']), 4)
        article = next(row for row in manifest['articles'] if row['article_id'] == 'article_1')
        self.assertEqual(article['pair_ids'], ['pair_1', 'pair_7'])
        self.assertEqual(article['query_ids'], ['query_1', 'query_7'])
        self.assertFalse((self.root / 'data/raw').exists())

    def test_balances_domain_origin_and_hosts_without_random_state(self):
        self.rows = []
        i = 0
        for domain in ('kesehatan', 'keuangan', 'teknologi'):
            for origin in ('google_only', 'google_and_gemini', 'gemini_only'):
                for _ in range(4):
                    i += 1
                    self.rows.append(source_pair(i, domain, origin))
        self.save_source()
        manifest = self.manifest()
        first = manifest['articles'][:9]
        groups = {(row['research_domains'][0], row['candidate_origins'][0]) for row in first}
        self.assertEqual(len(groups), 9)
        self.assertEqual(manifest, self.manifest())

    def test_path_and_url_safety(self):
        with self.assertRaises(ValueError):
            scraper.safe_path(self.root, '../outside')
        with self.assertRaises(ValueError):
            scraper.safe_path(self.root, '.')
        for url in ('http://localhost/a', 'http://127.0.0.1/a', 'http://10.0.0.1/a',
                    'file:///something', 'https://user:password@example.com/a',
                    'https://example.com:8000/a'):
            self.assertFalse(scraper.valid_public_url(url), url)
        self.assertTrue(scraper.valid_public_url('https://example.com/article'))

    def test_resume_does_not_retry_failures_and_explicit_retry_retains_history(self):
        manifest = self.manifest()
        calls = []

        def failing(url):
            calls.append(url)
            return {'status': 'network_error', 'final_url': url, 'body': b'', 'error_type': 'Timeout'}

        def success(url):
            calls.append(url)
            return {'status': 'success', 'final_url': url, 'http_status': 200,
                    'content_type': 'text/html', 'body': b'<html><article>Complete article</article></html>'}

        rows = scraper.collect(manifest, self.root, max_new_urls=1, fetcher=failing, extractor=fake_extract)
        self.assertEqual([row['scrape_status'] for row in rows].count('not_requested'), 2)
        self.assertEqual(len(calls), 1)
        scraper.collect(manifest, self.root, max_new_urls=2, fetcher=success, extractor=fake_extract)
        scraper.collect(manifest, self.root, max_new_urls=2, fetcher=success, extractor=fake_extract)
        self.assertEqual(len(calls), 3)
        rows = scraper.collect(manifest, self.root, max_new_urls=1, retry_failed=True,
                               fetcher=success, extractor=fake_extract)
        self.assertEqual(len(calls), 4)
        raw, interim = scraper.paths(manifest, self.root)
        record = scraper.load_record(raw, manifest['articles'][0])
        self.assertEqual([r['status'] for r in record['attempts']], ['network_error', 'success'])
        self.assertEqual(record['extraction']['n_words'], 150)
        self.assertTrue((self.root / record['attempts'][-1]['raw_html_path']).is_file())
        self.assertTrue((self.root / record['attempts'][-1]['extraction_path']).is_file())
        self.assertEqual(len(rows), 3)
        self.assertFalse((raw / 'running.lock').exists())
        self.assertTrue((interim / 'source_pairs.csv').exists())

    def test_error_response_body_saved_without_extracting_and_without_dropping_url(self):
        manifest = self.manifest()
        invoked = []

        def blocked(url):
            return {'status': 'http_error', 'http_status': 403, 'final_url': url,
                    'body': b'<html><title>Forbidden</title></html>', 'error_type': 'HTTP_403'}

        def extract(*args, **kwargs):
            invoked.append(args)
            return fake_extract(*args, **kwargs)

        rows = scraper.collect(manifest, self.root, 1, fetcher=blocked, extractor=extract)
        raw, _ = scraper.paths(manifest, self.root)
        record = scraper.load_record(raw, manifest['articles'][0])
        self.assertEqual(invoked, [])
        self.assertEqual(len(rows), 3)
        self.assertEqual(record['status'], 'http_error')
        self.assertTrue((self.root / record['attempts'][0]['raw_html_path']).is_file())

    def test_interrupt_keeps_attempt_marker_and_releases_lock(self):
        manifest = self.manifest()

        def interrupt(url):
            raise KeyboardInterrupt()

        with self.assertRaises(KeyboardInterrupt):
            scraper.collect(manifest, self.root, 1, fetcher=interrupt, extractor=fake_extract)
        raw, _ = scraper.paths(manifest, self.root)
        record = scraper.load_record(raw, manifest['articles'][0])
        self.assertEqual(record['status'], 'interrupted')
        self.assertFalse((raw / 'running.lock').exists())
        self.assertEqual(len(scraper.pending_articles(manifest, self.root)), 2)
        self.assertEqual(len(scraper.pending_articles(manifest, self.root, retry_failed=True)), 1)

    def test_changed_manifest_and_concurrent_run_are_refused(self):
        manifest = self.manifest()
        raw, _ = scraper.paths(manifest, self.root)
        write_json(raw / 'manifest.json', {**manifest, 'pipeline_version': 999})
        with self.assertRaisesRegex(ValueError, 'Manifest berubah'):
            scraper.collect(manifest, self.root, 1, fetcher=lambda url: None, extractor=fake_extract)
        write_json(raw / 'manifest.json', manifest)
        (raw / 'running.lock').write_text('another process', encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, 'terkunci'):
            scraper.collect(manifest, self.root, 1, fetcher=lambda url: None, extractor=fake_extract)

    def test_extraction_error_preserves_download_and_marks_retry(self):
        manifest = self.manifest()

        def fetch(url):
            return {'status': 'success', 'final_url': url, 'content_type': 'text/html', 'body': b'<html>Downloaded</html>'}

        def extract(*args, **kwargs):
            raise ValueError('malformed page')

        scraper.collect(manifest, self.root, 1, fetcher=fetch, extractor=extract)
        raw, _ = scraper.paths(manifest, self.root)
        record = scraper.load_record(raw, manifest['articles'][0])
        self.assertEqual(record['status'], 'extraction_error')
        self.assertTrue((self.root / record['attempts'][0]['raw_html_path']).exists())


class FakeResponse:
    def __init__(self, status=200, body=b'', headers=None):
        self.status_code, self.body = status, body
        self.headers = headers or {'Content-Type': 'text/html; charset=utf-8'}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def iter_content(self, chunk_size):
        for offset in range(0, len(self.body), chunk_size):
            yield self.body[offset:offset + chunk_size]


class FakeSession:
    def __init__(self, responses):
        self.responses = dict(responses)
        self.headers, self.calls = {}, []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        return response

    def close(self):
        pass


@unittest.skipIf(scraper.requests is None, 'requests dependency not installed')
class DirectHttpTests(unittest.TestCase):
    def client(self, responses, **config):
        session = FakeSession(responses)
        client = scraper.DirectFetcher({'per_host_delay_seconds': 0, **config}, session=session,
                                       sleeper=lambda seconds: None)
        return client, session

    def test_robots_disallow_stops_before_article_request(self):
        client, session = self.client({'https://example.com/robots.txt': FakeResponse(
            body=b'User-agent: *\nDisallow: /private\n', headers={'Content-Type': 'text/plain'})})
        result = client.fetch('https://example.com/private/article')
        self.assertEqual(result['status'], 'robots_disallowed')
        self.assertEqual([url for url, _ in session.calls], ['https://example.com/robots.txt'])
        self.assertIn('Disallow: /private', result['robots_checks'][0]['robots_text'])

    def test_missing_robots_allows_page_and_caches_per_origin(self):
        client, session = self.client({
            'https://example.com/robots.txt': FakeResponse(404),
            'https://example.com/a': FakeResponse(body=b'<html>A</html>'),
            'https://example.com/b': FakeResponse(body=b'<html>B</html>')})
        self.assertEqual(client.fetch('https://example.com/a')['status'], 'success')
        self.assertEqual(client.fetch('https://example.com/b')['status'], 'success')
        self.assertEqual(len(session.calls), 3)
        self.assertTrue(all(not options['allow_redirects'] and options['stream'] for _, options in session.calls))

    def test_robots_server_error_is_uncertainty_not_permission(self):
        client, session = self.client({'https://example.com/robots.txt': FakeResponse(503)})
        result = client.fetch('https://example.com/a')
        self.assertEqual(result['status'], 'robots_unavailable')
        self.assertEqual(len(session.calls), 1)

    def test_redirect_checks_new_host_robots_before_fetching(self):
        client, session = self.client({
            'https://example.com/robots.txt': FakeResponse(404),
            'https://example.com/a': FakeResponse(302, headers={'Location': 'https://other.example/private'}),
            'https://other.example/robots.txt': FakeResponse(body=b'User-agent: *\nDisallow: /\n')})
        result = client.fetch('https://example.com/a')
        self.assertEqual(result['status'], 'robots_disallowed')
        self.assertEqual(len(result['redirect_history']), 1)
        self.assertNotIn('https://other.example/private', [url for url, _ in session.calls])

    def test_redirect_to_private_destination_is_not_requested(self):
        client, session = self.client({
            'https://example.com/robots.txt': FakeResponse(404),
            'https://example.com/a': FakeResponse(302, headers={'Location': 'http://127.0.0.1/private'})})
        result = client.fetch('https://example.com/a')
        self.assertEqual(result['status'], 'invalid_url')
        self.assertEqual(len(session.calls), 2)

    def test_content_type_challenge_and_http_failure_have_distinct_status(self):
        cases = [
            (FakeResponse(body=b'%PDF-', headers={'Content-Type': 'application/pdf'}), 'non_html'),
            (FakeResponse(body=b'<html><title>Just a moment...</title></html>'), 'blocked_or_challenge'),
            (FakeResponse(403, b'<html>Forbidden</html>'), 'http_error'),
            (FakeResponse(body=b'<html><title>Cara menggunakan CAPTCHA</title></html>'), 'success')]
        for response, expected in cases:
            with self.subTest(expected=expected):
                client, _ = self.client({'https://example.com/robots.txt': FakeResponse(404),
                                         'https://example.com/a': response})
                result = client.fetch('https://example.com/a')
                self.assertEqual(result['status'], expected)
                self.assertEqual(result['body'], response.body)

    def test_timeout_no_automatic_retry_and_error_text_not_leaked(self):
        client, session = self.client({
            'https://example.com/robots.txt': FakeResponse(404),
            'https://example.com/a': scraper.requests.Timeout('secret-token=private')})
        result = client.fetch('https://example.com/a')
        self.assertEqual(result['status'], 'network_error')
        self.assertEqual(result['error_type'], 'Timeout')
        self.assertNotIn('secret-token', json.dumps({k: v for k, v in result.items() if k != 'body'}))
        self.assertEqual(len(session.calls), 2)

    def test_max_download_bytes_enforced(self):
        client, _ = self.client({'https://example.com/robots.txt': FakeResponse(404),
                                 'https://example.com/a': FakeResponse(body=b'a' * 100)}, max_bytes=50)
        result = client.fetch('https://example.com/a')
        self.assertEqual(result['status'], 'response_too_large')
        self.assertLessEqual(len(result['body']), 50)


if __name__ == '__main__':
    unittest.main()
