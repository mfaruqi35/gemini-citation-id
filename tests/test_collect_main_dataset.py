"""Contract tests for main collection; all external calls are simulated."""

import copy
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import collect_main_dataset as main
from test_pilot_gemini_grounding import response, resolve


class MainDatasetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / 'data'
        config = main.read_json(main.ROOT / 'configs/main_dataset.json')
        self.manifest = {'config': config, 'pipeline_version': 1, 'queries': [{
            'query_id': 'query_test', 'query_text': 'Pertanyaan asli?', 'domain': 'kesehatan',
            'selection_status': 'accepted', 'language': 'id'}]}
        self.calls = {'google': 0, 'gemini': 0, 'quota': 0}

    def tearDown(self):
        self.tmp.cleanup()

    def google(self, endpoint, parameters, key):
        self.calls['google'] += 1
        self.assertEqual(parameters['q'], 'Pertanyaan asli?')
        return {'search_metadata': {'status': 'Success'}, 'organic_results': [
            {'position': 1, 'link': 'https://example.com/a', 'title': 'A'},
            {'position': 2, 'link': 'https://example.com/b', 'title': 'B'}]}

    def gemini(self, model, request, key):
        self.calls['gemini'] += 1
        self.assertEqual(request['tools'], [{'google_search': {}}])
        self.assertEqual(request['contents'][0]['parts'][0]['text'], 'Pertanyaan asli?')
        result = response()
        # Two valid trials with distinct cited URLs, third lacks grounding.
        if self.calls['gemini'] == 2:
            result['candidates'][0]['groundingMetadata']['groundingSupports'][0]['groundingChunkIndices'] = [1]
        if self.calls['gemini'] == 3:
            result['candidates'][0].pop('groundingMetadata')
        return result

    def account(self, key):
        self.calls['quota'] += 1
        return {'total_searches_left': 250}

    def collect(self, **overrides):
        arguments = dict(fetcher=self.google, generator=self.gemini, resolver=resolve, quota_reader=self.account)
        arguments.update(overrides)
        return main.collect(self.manifest, self.data, 'secret-serp', 'secret-gemini', **arguments)

    def record_path(self):
        return self.data / 'raw/main/main_01/queries/query_test.json'

    def test_three_attempts_two_valid_and_idempotent_resume(self):
        rows = self.collect()
        self.assertEqual(self.calls, {'google': 1, 'gemini': 3, 'quota': 1})
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(row['n_valid'], 2)
            self.assertEqual(row['n_scheduled'], 3)
            self.assertEqual(row['n_cited'], 1)
            self.assertEqual(row['citation_proportion'], 0.5)
            self.assertEqual(row['citation_label'], '')
            self.assertTrue(row['grounding_eligible'])
            self.assertTrue(row['collection_complete'])
            self.assertFalse(row['ready_for_model'])
        self.collect()
        self.assertEqual(self.calls, {'google': 1, 'gemini': 3, 'quota': 1})
        self.manifest['config']['repetitions'] = 4
        with self.assertRaises(ValueError):
            self.collect()

    def test_insufficient_valid_is_not_negative(self):
        self.collect()
        record = main.read_json(self.record_path())
        record['trials'][1]['response']['candidates'][0]['finishReason'] = 'MAX_TOKENS'
        main.write_json(self.record_path(), record)
        rows = main.export_dataset(self.manifest, self.data)
        self.assertTrue(all(row['n_valid'] == 1 and not row['grounding_eligible'] for row in rows))
        self.assertTrue(all(row['citation_label'] == '' for row in rows))

    def test_unknown_cited_destination_is_not_negative(self):
        self.collect()
        record = main.read_json(self.record_path())
        record['trials'][1]['url_resolutions']['https://example.com/b'] = {
            'resolution_status': 'network_or_url_error', 'resolved_url': ''}
        main.write_json(self.record_path(), record)
        rows = main.export_dataset(self.manifest, self.data)
        self.assertTrue(all(row['citation_label'] == '' and row['citation_proportion'] == '' for row in rows))
        self.assertEqual(rows[0]['n_unknown_matches'], 1)
        self.assertEqual(rows[0]['citation_lower'], 0.5)
        self.assertEqual(rows[0]['citation_upper'], 1.0)
        self.assertEqual(rows[1]['citation_lower'], 0)
        self.assertEqual(rows[1]['citation_upper'], 0.5)

    def test_resume_response_saved_without_regeneration(self):
        def interrupted(url):
            if self.calls['gemini']:
                raise KeyboardInterrupt()
            return resolve(url)
        with self.assertRaises(KeyboardInterrupt):
            self.collect(resolver=interrupted)
        self.assertEqual(main.read_json(self.record_path())['trials'][0]['status'], 'response_saved')
        self.collect()
        self.assertEqual(self.calls['google'], 1)
        self.assertEqual(self.calls['gemini'], 3)

    def test_api_error_counts_as_one_slot_without_retry(self):
        def fail(*args):
            self.calls['gemini'] += 1
            raise main.GenerationError(429)
        with self.assertRaises(main.GenerationError):
            self.collect(generator=fail)
        self.collect()
        self.assertEqual(self.calls['gemini'], 3)
        record = main.read_json(self.record_path())
        self.assertEqual(record['trials'][0]['status'], 'error')
        self.assertEqual(len(record['trials']), 3)

    def test_quota_reserve_stops_before_search(self):
        with self.assertRaises(RuntimeError):
            self.collect(quota_reader=lambda key: {'total_searches_left': 10})
        self.assertEqual(self.calls['google'], 0)
        self.assertEqual(self.calls['gemini'], 0)

    def test_final_slot_error_completes_checkpoint_without_fourth_attempt(self):
        def generator(*args):
            if self.calls['gemini'] == 2:
                self.calls['gemini'] += 1
                raise main.GenerationError(429, {'status': 'RESOURCE_EXHAUSTED'})
            return self.gemini(*args)
        with self.assertRaises(main.GenerationError):
            self.collect(generator=generator)
        record = main.read_json(self.record_path())
        self.assertEqual(record['status'], 'completed')
        self.assertEqual(record['trials'][2]['error_details'], {'status': 'RESOURCE_EXHAUSTED'})
        self.collect(generator=generator)
        self.assertEqual(self.calls['gemini'], 3)

    def test_collection_window_blocks_labels(self):
        self.collect()
        record = main.read_json(self.record_path())
        record['google']['started_at'] = '2000-01-01T00:00:00+00:00'
        main.write_json(self.record_path(), record)
        self.manifest['config']['citation_threshold'] = 0.5
        rows = main.export_dataset(self.manifest, self.data)
        self.assertTrue(all(not row['within_time_window'] and row['citation_label'] == '' for row in rows))

    def test_url_and_organic_rules(self):
        self.assertEqual(main.normalize_url('https://EXAMPLE.com:443/a?id=2&utm_source=test#part'), 'https://example.com/a?id=2')
        self.assertNotEqual(main.normalize_url('http://example.com/a'), main.normalize_url('https://example.com/a'))
        self.assertNotEqual(main.normalize_url('https://example.com/A'), main.normalize_url('https://example.com/a'))
        self.assertNotEqual(main.normalize_url('https://example.com/a'), main.normalize_url('https://example.com/a/'))
        self.assertEqual(main.normalize_url('https://example.com:invalid/a'), '')
        rows = [{'position': n, 'link': 'https://example.com/a'} for n in range(1, 13)]
        rows.extend([rows[0], None, {'position': '1', 'link': 'https://example.com/x'}])
        self.assertEqual(len(main.organic_rows({'response': {'organic_results': rows}})), 10)

    def read_export(self, name):
        return main.read_rows(self.data / 'interim/main/main_01' / (name + '.csv'))

    def test_union_includes_all_cited_urls_and_counts_once_per_trial(self):
        def generator(*args):
            result = self.gemini(*args)
            if self.calls['gemini'] == 1:
                meta = result['candidates'][0]['groundingMetadata']
                meta['groundingChunks'].extend([
                    {'web': {'uri': 'https://example.com/c', 'title': 'C'}},
                    {'web': {'uri': 'https://example.com/c', 'title': 'C repeated'}},
                    {'web': {'uri': 'https://example.com/uncited', 'title': 'Not cited'}}])
                meta['groundingSupports'][0]['groundingChunkIndices'] = [0, 2, 3]
            return result
        self.collect(generator=generator)
        self.assertEqual(len(self.read_export('query_article_pairs')), 2)
        union = self.read_export('query_article_pairs_union')
        self.assertEqual(len(union), 3)
        added = next(r for r in union if r['article_url'].endswith('/c'))
        self.assertEqual(added['candidate_origin'], 'gemini_only')
        self.assertEqual(added['google_positions'], '[]')
        self.assertEqual(added['google_title'], '')
        self.assertEqual(added['article_title'], 'C')
        self.assertEqual(added['n_cited'], '1')
        self.assertEqual(added['n_valid'], '2')
        self.assertEqual(added['citation_proportion'], '0.5')
        self.assertFalse(any(r['article_url'].endswith('/uncited') for r in union))

    def test_invalid_trial_sources_preserved_but_not_used_for_union(self):
        def generator(*args):
            self.calls['gemini'] += 1
            result = response()
            if self.calls['gemini'] == 3:
                result['candidates'][0]['finishReason'] = 'MAX_TOKENS'
                result['candidates'][0]['groundingMetadata']['groundingChunks'][0]['web']['uri'] = 'https://example.com/invalid-only'
            return result
        self.collect(generator=generator)
        self.assertTrue(any(r['source_url'].endswith('/invalid-only') for r in self.read_export('sources')))
        self.assertFalse(any(r['article_url'].endswith('/invalid-only') for r in self.read_export('query_article_pairs_union')))

    def test_union_does_not_assume_every_added_source_has_positive_threshold_label(self):
        self.manifest['config']['citation_threshold'] = 0.5
        def generator(*args):
            self.calls['gemini'] += 1
            result = response()
            if self.calls['gemini'] == 1:
                result['candidates'][0]['groundingMetadata']['groundingChunks'][0]['web']['uri'] = 'https://example.com/c'
            return result
        self.collect(generator=generator)
        row = next(r for r in self.read_export('query_article_pairs_union') if r['article_url'].endswith('/c'))
        self.assertEqual(row['n_cited'], '1')
        self.assertEqual(row['n_valid'], '3')
        self.assertEqual(row['citation_label'], '0')

    def test_unresolved_cited_source_stays_in_audit_and_blocks_false_negative(self):
        def generator(*args):
            result = self.gemini(*args)
            if self.calls['gemini'] == 1:
                result['candidates'][0]['groundingMetadata']['groundingChunks'][0]['web']['uri'] = 'https://example.com/unresolved'
            return result
        def resolver(url):
            return {'resolved_url': '', 'resolution_status': 'network_or_url_error'} if url.endswith('/unresolved') else resolve(url)
        self.collect(generator=generator, resolver=resolver)
        union = self.read_export('query_article_pairs_union')
        self.assertEqual(len(union), 2)
        self.assertTrue(any(r['source_url'] == '' and r['is_cited'] == 'True' for r in self.read_export('sources')))
        self.assertTrue(all(r['n_unknown_matches'] == '1' and r['citation_label'] == '' for r in union))


if __name__ == '__main__':
    unittest.main()
