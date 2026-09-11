"""Local extraction, deduplication, lineage, and persistent review tests."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import prepare_query_expansion as expansion
from collect_paa import write_json, write_csv


class ExpansionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config = {'expansion_id': 'extra', 'paa_batches': ['paa_extra'],
                       'main_batches': ['main_test'], 'existing_pool': 'data/original.csv'}
        write_csv(self.root / 'data/original.csv', [{'query_id': 'known', 'query_text': 'APA ITU BANK?'}],
                  ['query_id', 'query_text'])
        job = {'request_id': 'request', 'research_domain': 'keuangan', 'topic_id': 'topic_bank',
               'source_text': 'bank', 'parameters': {'q': 'bank'}}
        write_json(self.root / 'data/raw/paa/batches/paa_extra/manifest.json', {'jobs': [job]})
        write_json(self.root / 'data/raw/paa/requests/request.json', {
            'status': 'success', 'batch_id': 'paa_extra', 'retrieved_at': 'time', 'search_id': 'serp_1',
            'response': {'related_questions': [{'question': 'Apa itu bank?'},
                                              {'question': 'Bagaimana cara menabung?'},
                                              {'question': 'Bagaimana cara menabung?'}]}})
        self.main_path = self.root / 'data/raw/main/main_test/queries/parent.json'
        write_json(self.main_path, {
            'query': {'query_id': 'parent', 'query_text': 'Tabungan itu apa?', 'topic_id': 'topic_bank',
                      'domain': 'keuangan', 'source_type': 'people_also_ask'},
            'google': {'started_at': 'time', 'response': {'search_metadata': {'id': 'serp_2', 'status': 'Success'},
                       'related_questions': [{'question': 'Bagaimana cara menabung?'}]}}})

    def tearDown(self):
        self.tmp.cleanup()

    def test_original_text_deduplication_and_parent_lineage(self):
        before = self.main_path.read_bytes()
        rows = expansion.prepare(self.config, root=self.root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['query_text'], 'Bagaimana cara menabung?')
        self.assertEqual(rows[0]['n_source_occurrences'], 3)
        self.assertEqual(rows[0]['selection_status'], 'pending')
        pool = expansion.read_rows(self.root / 'data/interim/query_expansion/extra/source_pool.csv')
        child = next(r for r in pool if r['parent_query_id'] == 'parent')
        self.assertEqual(child['topic_id'], 'topic_bank')
        self.assertEqual(child['paa_depth'], '2')
        self.assertEqual(self.main_path.read_bytes(), before)

    def test_review_persists_and_no_automatic_language_acceptance(self):
        rows = expansion.prepare(self.config, root=self.root)
        qid = rows[0]['query_id']
        change = {'language': 'id', 'status': 'accepted', 'reason': 'Informasi jelas.', 'reviewer': 'assistant'}
        expansion.prepare(self.config, {qid: change}, self.root)
        result = expansion.prepare(self.config, root=self.root)
        self.assertEqual(result[0]['selection_status'], 'accepted')
        with self.assertRaises(ValueError):
            expansion.prepare(self.config, {qid: {**change, 'language': 'unknown'}}, self.root)

    def test_unknown_review_id_rejected(self):
        with self.assertRaises(ValueError):
            expansion.prepare(self.config, {'missing': {'language': 'id', 'status': 'accepted',
                              'reason': 'test', 'reviewer': 'assistant'}}, self.root)


if __name__ == '__main__':
    unittest.main()
