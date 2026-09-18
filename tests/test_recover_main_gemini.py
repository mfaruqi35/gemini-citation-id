"""Recovery tests use simulated API responses and temporary checkpoints only."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import recover_main_gemini as recovery
import pilot_gemini_grounding as pilot
from test_pilot_gemini_grounding import response, resolve


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / 'data'
        config = recovery.read_json(recovery.ROOT / 'configs/main_dataset_02.json')
        query = {'query_id': 'test', 'query_text': 'Pertanyaan?', 'domain': 'keuangan'}
        self.manifest = {'config': config, 'queries': [query], 'pipeline_version': 1}
        self.raw = self.data / 'raw/main' / config['dataset_id']
        self.path = self.raw / 'queries/test.json'
        self.record = {'query': query, 'status': 'completed',
                       'google': {'status': 'completed', 'started_at': recovery.now()}, 'trials': [
                           {'trial_id': 't1', 'repetition': 1, 'status': 'completed',
                            'started_at': recovery.now(), 'response': response()},
                           {'trial_id': 't2', 'repetition': 2, 'status': 'error',
                            'started_at': recovery.now(), 'error': 'network_or_timeout'},
                           {'trial_id': 't3', 'repetition': 3, 'status': 'error',
                            'started_at': recovery.now(), 'error': 'network_or_timeout'}]}
        recovery.write_json(self.raw / 'manifest.json', self.manifest)
        recovery.write_json(self.path, self.record)

    def tearDown(self):
        self.tmp.cleanup()

    def run_recovery(self, generator, limit=2, resolver=resolve):
        return recovery.recover(self.manifest, self.data, 'fake', limit,
                                generator=generator, resolver=resolver)

    def test_recovers_only_failed_slots_and_retains_history(self):
        with patch.object(pilot, 'urlopen', side_effect=AssertionError('No network')):
            calls = []
            def generate(*args):
                calls.append(args)
                return response()
            self.assertEqual(self.run_recovery(generate), 2)
            saved = recovery.read_json(self.path)
            self.assertEqual(saved['google'], self.record['google'])
            self.assertEqual(saved['trials'][0], self.record['trials'][0])
            self.assertEqual(len(saved['trials']), 3)
            self.assertEqual(saved['trials'][1]['recovery_history'][0]['trial'], self.record['trials'][1])
            self.assertEqual(self.run_recovery(generate), 0)
            self.assertEqual(len(calls), 2)
            self.assertFalse((self.raw / 'running.lock').exists())

    def test_budget_caps_new_calls(self):
        self.assertEqual(self.run_recovery(lambda *a: response(), limit=1), 1)
        saved = recovery.read_json(self.path)
        self.assertEqual(saved['trials'][2], self.record['trials'][2])

    def test_failed_retry_cannot_repeat_across_runs(self):
        def fail(*a):
            raise pilot.GenerationError('timeout')
        with self.assertRaises(pilot.GenerationError):
            self.run_recovery(fail)
        saved = recovery.read_json(self.path)
        self.assertEqual(recovery.recovery_reason(saved, saved['trials'][1], self.manifest['config']), 'retry_limit_reached')
        self.assertEqual(self.run_recovery(lambda *a: response()), 1)
        self.assertFalse((self.raw / 'running.lock').exists())

    def test_expired_window_and_billing_are_not_retried(self):
        self.record['google']['started_at'] = '2000-01-01T00:00:00+00:00'
        self.record['trials'][2]['error'] = '429'
        recovery.write_json(self.path, self.record)
        def unexpected(*a):
            self.fail('API must not be called')
        self.assertEqual(self.run_recovery(unexpected), 0)
        self.assertEqual(recovery.read_json(self.path), self.record)

    def test_resolution_resume_does_not_generate_again(self):
        def interrupted(url):
            raise RuntimeError('interrupted resolver')
        with self.assertRaises(RuntimeError):
            self.run_recovery(lambda *a: response(), limit=1, resolver=interrupted)
        saved = recovery.read_json(self.path)
        self.assertEqual(saved['trials'][1]['status'], 'response_saved')
        # Other failed slot cannot be retried, so only cached response resumes.
        saved['trials'][2]['error'] = '429'
        recovery.write_json(self.path, saved)
        def unexpected(*a):
            self.fail('Saved response must not be generated again')
        self.assertEqual(self.run_recovery(unexpected), 0)
        self.assertEqual(recovery.read_json(self.path)['trials'][1]['status'], 'completed')

    def test_tmp_and_lock_block_requests(self):
        recovery.write_json(self.path.with_suffix('.tmp'), {'response': 'unsaved'})
        with self.assertRaises(ValueError):
            self.run_recovery(lambda *a: self.fail('API'))
        self.assertFalse((self.raw / 'running.lock').exists())
        recovery.write_json(self.raw / 'running.lock', {'running': True})
        with self.assertRaises(FileExistsError):
            self.run_recovery(lambda *a: self.fail('API'))

    def test_timeout_is_120_and_errors_are_distinguished_without_secrets(self):
        for error, expected in [(TimeoutError('secret'), 'timeout'),
                                (URLError(TimeoutError('secret')), 'timeout'),
                                (URLError(OSError('secret')), 'network_error')]:
            with patch.object(pilot, 'urlopen', side_effect=error) as opened:
                with self.assertRaises(pilot.GenerationError) as caught:
                    pilot.generate('test', {}, 'secret')
                self.assertEqual(opened.call_args.kwargs['timeout'], 120)
                self.assertEqual(caught.exception.code, expected)
                self.assertNotIn('secret', str(caught.exception.details))


if __name__ == '__main__':
    unittest.main()
