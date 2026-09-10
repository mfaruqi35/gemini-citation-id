"""Uji tanpa jaringan untuk menjaga kuota dan jejak sumber."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from collect_paa import collect, plan, read_json, sanitize, ROOT


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / "data"
        self.manifest = plan(read_json(ROOT / "configs/paa_pilot.json"),
                             ROOT / "data/interim/review/needs_paa.csv")
        self.manifest["jobs"] = self.manifest["jobs"][:2]

    def tearDown(self):
        self.tmp.cleanup()

    def test_resume_and_empty_paa_do_not_spend_twice(self):
        calls = []

        def fake(endpoint, params, key):
            calls.append(params["q"])
            return {"search_metadata": {"status": "Success", "id": "test"},
                    "related_questions": ([{"question": "Apa pengertiannya?", "type": "featured_snippet"}]
                                          if len(calls) == 1 else [])}

        quota = lambda key: {"total_searches_left": 30}
        questions, searches = collect(self.manifest, self.data, "fake", fake, quota)
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(questions), 1)
        self.assertEqual(searches[1]["status"], "no_paa")
        self.assertEqual(questions[0]["topic_id"], self.manifest["jobs"][0]["topic_id"])
        collect(self.manifest, self.data, "fake", fake, quota)
        self.assertEqual(len(calls), 2)

    def test_insufficient_quota_sends_no_search(self):
        def forbidden(*args):
            self.fail("Search should not be sent")
        with self.assertRaises(RuntimeError):
            collect(self.manifest, self.data, "fake", forbidden,
                    lambda key: {"total_searches_left": 1})
        self.assertFalse((self.data / "raw/paa/requests").exists())

    def test_failure_is_recorded_and_not_retried(self):
        calls = []

        def failed(*args):
            calls.append(1)
            raise RuntimeError("simulated failure")

        quota = lambda key: {"total_searches_left": 30}
        with self.assertRaises(RuntimeError):
            collect(self.manifest, self.data, "fake", failed, quota)
        with self.assertRaises(RuntimeError):
            collect(self.manifest, self.data, "fake", failed, quota)
        # Second run only attempts the second job, not the failed first job.
        self.assertEqual(len(calls), 2)
        collect(self.manifest, self.data, "fake", failed, quota)
        self.assertEqual(len(calls), 2)
        records = [read_json(p) for p in (self.data / "raw/paa/requests").glob("*.json")]
        self.assertTrue(all(r["status"] == "error" for r in records))

    def test_secrets_are_redacted(self):
        data = {"api_key": "SECRET", "url": "https://serpapi.com/search?api_key=SECRET&q=test",
                "nested": ["SECRET"]}
        self.assertNotIn("SECRET", json.dumps(sanitize(data, "SECRET")))


if __name__ == "__main__":
    unittest.main()
