"""Windows file-lock retries must never discard the latest checkpoint."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from collect_paa import write_json, write_csv


class FileWriteTests(unittest.TestCase):
    def test_transient_lock_retries_replacement(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "trial.json"
            path.write_text('{"status": "started"}', encoding="utf-8")
            original = Path.replace
            calls = []
            def locked_then_ok(temp, target):
                calls.append(1)
                if len(calls) < 3:
                    raise PermissionError("simulated Windows lock")
                return original(temp, target)
            with patch.object(Path, "replace", locked_then_ok), patch("collect_paa.time.sleep") as sleep:
                write_json(path, {"status": "response_saved", "response": {"test": True}})
            self.assertEqual(len(calls), 3)
            self.assertEqual(sleep.call_count, 2)
            self.assertEqual(json.loads(path.read_text())["status"], "response_saved")
            self.assertFalse(path.with_suffix(".tmp").exists())

    def test_persistent_lock_retains_old_json_and_new_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "trial.json"
            path.write_text('{"status": "started"}', encoding="utf-8")
            with patch.object(Path, "replace", side_effect=PermissionError("locked")) as replace, patch("collect_paa.time.sleep"):
                with self.assertRaises(PermissionError):
                    write_json(path, {"status": "response_saved"})
            self.assertEqual(replace.call_count, 7)
            self.assertEqual(json.loads(path.read_text())["status"], "started")
            self.assertEqual(json.loads(path.with_suffix(".tmp").read_text())["status"], "response_saved")

    def test_csv_uses_same_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "trials.csv"
            original = Path.replace
            calls = []
            def locked_once(temp, target):
                calls.append(1)
                if len(calls) == 1:
                    raise PermissionError("locked")
                return original(temp, target)
            with patch.object(Path, "replace", locked_once), patch("collect_paa.time.sleep"):
                write_csv(path, [{"status": "completed"}], ["status"])
            self.assertIn("completed", path.read_text(encoding="utf-8-sig"))
            self.assertEqual(len(calls), 2)
