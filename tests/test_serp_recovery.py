import json
import socket
import ssl
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import collect_paa as paa
from recover_main_google import recover


class NetworkDiagnosticsTests(unittest.TestCase):
    def test_distinguishes_timeout_dns_and_certificate_without_secrets(self):
        cases = [(TimeoutError('secret-key'), 'timeout'),
                 (socket.gaierror(11001, 'secret-key'), 'dns_error'),
                 (ssl.SSLCertVerificationError(1, 'secret-key'), 'tls_certificate_error')]
        for reason, expected in cases:
            with self.subTest(expected=expected), patch.object(paa, 'urlopen', side_effect=URLError(reason)) as request:
                with self.assertRaises(paa.SerpApiError) as caught:
                    paa.fetch('search.json', {'q': 'test'}, 'secret-key')
                self.assertEqual(caught.exception.code, expected)
                self.assertNotIn('secret-key', str(caught.exception) + json.dumps(caught.exception.details))
                self.assertEqual(request.call_count, 1)
                self.assertEqual(request.call_args.kwargs['timeout'], 120)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / 'data'
        config = paa.read_json(paa.ROOT / 'configs/main_dataset.json')
        query = {'query_id': 'query_test', 'query_text': 'Pertanyaan asli?', 'domain': 'kesehatan'}
        self.manifest = {'config': config, 'queries': [query], 'pipeline_version': 1}
        raw = self.data / 'raw/main/main_01'
        paa.write_json(raw / 'manifest.json', self.manifest)
        self.path = raw / 'queries/query_test.json'
        self.record = {'query': query, 'status': 'started', 'trials': [],
                       'google': {'status': 'error', 'started_at': '2026-09-11T01:30:00+00:00'}}
        paa.write_json(self.path, self.record)
        self.calls = 0

    def tearDown(self):
        self.tmp.cleanup()

    def fetch(self, endpoint, params, key):
        self.calls += 1
        self.assertEqual(params['q'], 'Pertanyaan asli?')
        self.assertNotIn('no_cache', params)
        return {'search_parameters': {'q': params['q']},
                'search_metadata': {'status': 'Success', 'created_at': '2026-09-11 01:30:01 UTC'},
                'organic_results': [{'position': 1, 'link': 'https://example.com/a'}]}

    def recover(self, **kwargs):
        options = {'fetcher': self.fetch, 'quota_reader': lambda key: {'total_searches_left': 195}}
        options.update(kwargs)
        return recover(self.manifest, self.data, 'query_test', 'secret-key', **options)

    def test_cached_recovery_retains_history_timestamp_and_is_idempotent(self):
        record = self.recover()
        self.assertEqual(record['google']['status'], 'response_saved')
        self.assertEqual(record['google']['started_at'], '2026-09-11T01:30:01+00:00')
        self.assertEqual(record['google_recovery_history'][0]['google'], self.record['google'])
        self.assertEqual(record['trials'], [])
        self.recover()
        self.assertEqual(self.calls, 1)

    def test_rejects_recovery_after_gemini_has_started(self):
        self.record['trials'] = [{'status': 'started'}]
        paa.write_json(self.path, self.record)
        with self.assertRaises(ValueError):
            self.recover()
        self.assertEqual(self.calls, 0)

    def test_failure_remains_checkpointed_without_automatic_retry(self):
        def fail(*args):
            self.calls += 1
            raise paa.SerpApiError('timeout', 'timeout', {'exception_type': 'TimeoutError'})
        with self.assertRaises(paa.SerpApiError):
            self.recover(fetcher=fail)
        self.assertEqual(self.calls, 1)
        record = paa.read_json(self.path)
        self.assertEqual(record['google']['error_code'], 'timeout')
        self.assertEqual(len(record['google_recovery_history']), 1)

    def test_quota_check_does_not_mutate_failed_checkpoint(self):
        before = self.path.read_bytes()
        with self.assertRaises(RuntimeError):
            self.recover(quota_reader=lambda key: {'total_searches_left': 0})
        self.assertEqual(self.calls, 0)
        self.assertEqual(self.path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
