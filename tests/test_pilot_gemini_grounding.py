"""Verifikasi pilot memakai respons simulasi; tidak memakai kuota API."""

import copy
import io
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pilot_gemini_grounding as pilot


def response():
    return {"modelVersion": "test-model", "candidates": [{
        "finishReason": "STOP", "content": {"parts": [{"text": "Jawaban uji."}]},
        "groundingMetadata": {
            "webSearchQueries": ["contoh"],
            "groundingChunks": [{"web": {"uri": "https://example.com/a", "title": "A"}},
                                {"web": {"uri": "https://example.com/b", "title": "B"}}],
            "groundingSupports": [{"groundingChunkIndices": [0, 99]}],
        }}], "usageMetadata": {"totalTokenCount": 10}}


def resolve(url):
    return {"raw_url": url, "resolved_url": url, "resolution_status": "resolved",
            "http_status": 200, "resolved_at": "test"}


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / "data"
        self.manifest = pilot.build_plan(pilot.read_json(pilot.ROOT / "configs/gemini_grounding_pilot.json"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_design_and_cap(self):
        self.assertEqual(len(self.manifest["jobs"]), 36)
        self.assertEqual(Counter(r["research_domain"] for r in self.manifest["selected_sources"]),
                         {"kesehatan": 3, "keuangan": 3, "teknologi": 3})
        self.assertEqual(len({j["trial_id"] for j in self.manifest["jobs"]}), 36)
        jobs = self.manifest["jobs"]
        a, b = jobs[:2]
        self.assertEqual(a["source"], b["source"])
        self.assertEqual(a["request"]["contents"], b["request"]["contents"])
        self.assertNotEqual(a["request"]["systemInstruction"], b["request"]["systemInstruction"])
        config = copy.deepcopy(self.manifest["config"])
        config["max_calls"] = 35
        with self.assertRaises(ValueError):
            pilot.build_plan(config)

    def test_sources_are_not_all_citations(self):
        _, _, web, cited, text = pilot.grounding(response())
        self.assertEqual(len(web), 2)
        self.assertEqual(cited, {0})
        self.assertTrue(text)
        _, _, web, cited, _ = pilot.grounding({"promptFeedback": {"blockReason": "SAFETY"}})
        self.assertFalse(web)
        self.assertFalse(cited)

    def test_http_quota_diagnostics_exclude_secrets_and_provider_message(self):
        payload = {'error': {'status': 'RESOURCE_EXHAUSTED', 'message': 'secret-key account data',
                   'details': [{'@type': 'type.googleapis.com/google.rpc.QuotaFailure',
                                'violations': [{'quotaId': 'RequestsPerDay', 'quotaMetric': 'requests',
                                                'quotaValue': '100', 'subject': 'private-project'}]},
                               {'@type': 'type.googleapis.com/google.rpc.RetryInfo', 'retryDelay': '60s'}]}}
        error = HTTPError('https://example.com/?key=secret-key', 429, 'limited', {},
                          io.BytesIO(json.dumps(payload).encode()))
        with patch.object(pilot, 'urlopen', side_effect=error):
            with self.assertRaises(pilot.GenerationError) as caught:
                pilot.generate('test-model', {}, 'secret-key')
        details = caught.exception.details
        self.assertEqual(details['status'], 'RESOURCE_EXHAUSTED')
        self.assertEqual(details['retry_delay'], '60s')
        self.assertEqual(details['quota_violations'][0]['quotaId'], 'RequestsPerDay')
        self.assertNotIn('private-project', json.dumps(details))
        self.assertNotIn('secret-key', json.dumps(details))

    def test_non_json_http_error_keeps_original_status(self):
        error = HTTPError('https://example.com', 503, 'unavailable', {}, io.BytesIO(b'<html>error</html>'))
        with patch.object(pilot, 'urlopen', side_effect=error):
            with self.assertRaises(pilot.GenerationError) as caught:
                pilot.generate('test-model', {}, 'secret-key')
        self.assertEqual(caught.exception.code, '503')
        self.assertEqual(caught.exception.details, {})

    def test_partial_resume_and_freeze(self):
        self.manifest["jobs"] = self.manifest["jobs"][:2]
        calls = []
        def fake(*args):
            calls.append(1)
            return response()
        pilot.run_pilot(self.manifest, self.data, "fake", 1, fake, resolve)
        self.assertEqual(len(calls), 1)
        rows = pilot.run_pilot(self.manifest, self.data, "fake", generator=fake, resolver=resolve)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(r["status"] == "completed" for r in rows))
        self.assertTrue(all(r["n_cited_sources"] == 1 for r in rows))
        pilot.run_pilot(self.manifest, self.data, "fake", generator=fake, resolver=resolve)
        self.assertEqual(len(calls), 2)
        changed = copy.deepcopy(self.manifest)
        changed["config"]["model"] = "changed"
        with self.assertRaises(ValueError):
            pilot.run_pilot(changed, self.data, "fake", generator=fake, resolver=resolve)

    def test_recover_resolution_without_regeneration(self):
        self.manifest["jobs"] = self.manifest["jobs"][:1]
        calls = []
        def fake(*args):
            calls.append(1)
            return response()
        def interrupted(url):
            raise KeyboardInterrupt()
        with self.assertRaises(KeyboardInterrupt):
            pilot.run_pilot(self.manifest, self.data, "fake", generator=fake, resolver=interrupted)
        records = list((self.data / "raw/gemini_pilot").rglob("trial_*.json"))
        self.assertEqual(pilot.read_json(records[0])["status"], "response_saved")
        pilot.run_pilot(self.manifest, self.data, "fake", generator=fake, resolver=resolve)
        self.assertEqual(len(calls), 1)

    def test_api_error_does_not_repeat(self):
        self.manifest["jobs"] = self.manifest["jobs"][:1]
        calls = []
        def failing(*args):
            calls.append(1)
            raise pilot.GenerationError(429)
        with self.assertRaises(pilot.GenerationError):
            pilot.run_pilot(self.manifest, self.data, "fake", generator=failing, resolver=resolve)
        rows = pilot.run_pilot(self.manifest, self.data, "fake", generator=failing, resolver=resolve)
        self.assertEqual(len(calls), 1)
        self.assertEqual(rows[0]["status"], "error")

    def test_url_only_retry_and_reader_export(self):
        self.manifest["jobs"] = self.manifest["jobs"][:1]
        calls = []
        def fake(*args):
            calls.append(1)
            return response()
        def failed_resolution(url):
            return {"raw_url": url, "resolved_url": "", "resolution_status": "network_or_url_error",
                    "http_status": "", "resolved_at": "test"}
        pilot.run_pilot(self.manifest, self.data, "fake", generator=fake, resolver=failed_resolution)
        output = self.data / "interim/gemini_pilot" / self.manifest['config']['experiment_id']
        import csv
        with (output / 'source_links.csv').open(encoding='utf-8-sig', newline='') as handle:
            links = list(csv.DictReader(handle))
        self.assertTrue(all(r['source_url'] == '' and 'raw_url' not in r for r in links))
        pilot.resolve_missing(self.manifest, self.data, resolver=resolve)
        self.assertEqual(len(calls), 1)
        with (output / 'source_links.csv').open(encoding='utf-8-sig', newline='') as handle:
            links = list(csv.DictReader(handle))
        self.assertTrue(all(r['source_url'].startswith('https://example.com/') for r in links))
        def forbidden(url):
            self.fail('Known destinations must not be fetched again')
        pilot.resolve_missing(self.manifest, self.data, resolver=forbidden)
        self.assertEqual(pilot.destination_url({'resolved_url': 'https://vertexaisearch.cloud.google.com/grounding-api-redirect/abc'}), '')


if __name__ == "__main__":
    unittest.main()
