"""Offline checks for resumable quota-limited collection and usage reporting."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import continue_main_dataset as runner


class ContinueTests(unittest.TestCase):
    def test_explicit_config_selects_requested_batch_in_preview(self):
        manifest = {'config': {'dataset_id': 'main_03', 'serp_quota_reserve': 10},
                    'queries': [{'query_id': 'q', 'domain': 'teknologi'}]}
        with patch.object(runner, 'prepare', return_value=manifest) as prepare, \
             patch.object(sys, 'argv', ['runner', '--config', 'configs/main_dataset_03.json']):
            runner.main()
        prepare.assert_called_once_with(Path('configs/main_dataset_03.json'))

    def test_unstarted_runner_leaves_existing_checkpoint_and_passes_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            manifest = {'config': {'dataset_id': 'test', 'serp_api_key_variable': 'TEST',
                                   'serp_quota_reserve': 10},
                        'queries': [{'query_id': q, 'domain': 'kesehatan'} for q in ['old', 'new']]}
            checkpoint = root / 'data/raw/main/test/queries/old.json'
            runner.write_json(checkpoint, {'status': 'started'})
            original = checkpoint.read_bytes()
            with patch.object(runner, 'ROOT', root), \
                 patch.object(runner, 'prepare', return_value=manifest), \
                 patch.object(runner, 'get_serp_key', return_value='fake'), \
                 patch.object(runner, 'load_key', return_value='fake'), \
                 patch.object(runner, 'monitor', return_value={'serpapi': {'total_searches_left': 11}}), \
                 patch.object(runner, 'collect') as collect, \
                 patch.object(sys, 'argv', ['runner', '--run', '--unstarted-only', '--max-queries', '1']):
                runner.main()
                collect.assert_called_once_with(manifest, root / 'data', 'fake', 'fake',
                                                max_queries=1, unstarted_only=True)
            self.assertEqual(checkpoint.read_bytes(), original)

    def test_unstarted_only_cannot_request_recovery(self):
        with patch.object(sys, 'argv', ['runner', '--unstarted-only', '--recover-gemini']):
            with self.assertRaises(SystemExit):
                runner.main()

    def test_usage_counts_saved_response_even_before_resolution(self):
        with tempfile.TemporaryDirectory() as folder:
            raw = Path(folder)
            runner.write_json(raw / 'queries/q.json', {'status': 'started', 'trials': [
                {'status': 'response_saved', 'response': {'usageMetadata': {
                    'promptTokenCount': 10, 'candidatesTokenCount': 20,
                    'thoughtsTokenCount': 30, 'totalTokenCount': 60}}},
                {'status': 'error', 'error': '429'}]})
            report = runner.usage(raw)
            self.assertEqual(report['totalTokenCount'], 60)
            self.assertEqual(report['responses_with_usage'], 1)
            self.assertEqual(report['error_trials'], 1)
            self.assertEqual(report['completed_queries'], 0)

    def test_quota_reserve_stops_new_searches(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest = {'config': {'dataset_id': 'test', 'serp_api_key_variable': 'TEST',
                                   'serp_quota_reserve': 10},
                        'queries': [{'query_id': 'q', 'domain': 'kesehatan'}]}
            with patch.object(runner, 'ROOT', Path(folder)), \
                 patch.object(runner, 'prepare', return_value=manifest), \
                 patch.object(runner, 'get_serp_key', return_value='fake'), \
                 patch.object(runner, 'load_key', return_value='fake'), \
                 patch.object(runner, 'monitor', return_value={'serpapi': {'total_searches_left': 10}}), \
                 patch.object(runner, 'collect') as collect, \
                 patch.object(sys, 'argv', ['runner', '--run']):
                runner.main()
                collect.assert_not_called()

    def test_runtime_reserve_can_use_remaining_quota_without_changing_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest = {'config': {'dataset_id': 'test', 'serp_api_key_variable': 'TEST',
                                   'serp_quota_reserve': 10},
                        'queries': [{'query_id': 'q', 'domain': 'kesehatan'}]}
            with patch.object(runner, 'ROOT', Path(folder)), \
                 patch.object(runner, 'prepare', return_value=manifest), \
                 patch.object(runner, 'get_serp_key', return_value='fake'), \
                 patch.object(runner, 'load_key', return_value='fake'), \
                 patch.object(runner, 'monitor', return_value={'serpapi': {'total_searches_left': 10}}), \
                 patch.object(runner, 'collect') as collect, \
                 patch.object(sys, 'argv', ['runner', '--run', '--unstarted-only',
                                            '--max-queries', '1', '--quota-reserve', '0']):
                runner.main()
                collect.assert_called_once_with(manifest, Path(folder) / 'data', 'fake', 'fake',
                                                max_queries=1, unstarted_only=True,
                                                quota_reserve_override=0)
            self.assertEqual(manifest['config']['serp_quota_reserve'], 10)


if __name__ == '__main__':
    unittest.main()
