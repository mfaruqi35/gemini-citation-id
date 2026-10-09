import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from article_source_matching import ArticleIdentities, reconcile_pairs
from collect_paa import write_json
from pilot_gemini_grounding import resolve_url


def article(aid, url, canonical, text=None):
    return {'article_id': aid, 'article_url': url, 'final_url': url, 'canonical_url': canonical,
            'crawl_status': 'success', 'article_eligible': True, 'title': 'Judul artikel',
            'text': text or 'isi artikel bahasa Indonesia kesehatan ' * 40}


def trial(urls, resolved):
    return {'status': 'completed', 'url_resolutions': resolved, 'response': {'candidates': [{
        'finishReason': 'STOP', 'content': {'parts': [{'text': 'Jawaban'}]},
        'groundingMetadata': {'groundingChunks': [{'web': {'uri': u}} for u in urls],
                              'groundingSupports': [{'groundingChunkIndices': list(range(len(urls)))}]}}]}}


class MatchingTests(unittest.TestCase):
    def test_identical_canonical_content_confirms_alias_but_different_content_does_not(self):
        url = 'https://example.com/story'
        rows = [article('a', url, url), article('b', url + '?srsltid=abc', url)]
        ids = ArticleIdentities(rows)
        self.assertEqual(ids.identity(rows[0]['article_url']), ids.identity(rows[1]['article_url']))
        self.assertEqual(ids.unresolved, set())
        rows[1]['text'] = 'Different content ' * 130
        ids = ArticleIdentities(rows)
        self.assertNotEqual(ids.identity(rows[0]['article_url']), ids.identity(rows[1]['article_url']))
        self.assertEqual(ids.unresolved, {'a', 'b'})

    def test_saved_trials_relabel_deduplicate_per_trial_and_preserve_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            url, alias = 'https://example.com/story', 'https://example.com/story?srsltid=abc'
            articles = [article('a', url, url), article('b', alias, url)]
            base = {'source_batch': 'main_test', 'query_id': 'q', 'n_valid': '3', 'n_cited': '0',
                    'n_unknown_matches': '1', 'citation_proportion': '', 'in_google_top10': 'True',
                    'in_gemini_citations': 'False', 'candidate_origin': 'google_only'}
            pairs = [{**base, 'pair_id': 'p1', 'article_id': 'a', 'article_url': url},
                     {**base, 'pair_id': 'p2', 'article_id': 'b', 'article_url': alias}]
            saved = copy.deepcopy(pairs)
            target = {'resolved_url': alias}
            record = {'trials': [trial(['r1','r2'], {'r1': target, 'r2': target}),
                                 trial(['r3'], {}), trial(['r4'], {'r4': {'resolved_url': 'https://other.com/a'}})]}
            path = root / 'data/raw/main/main_test/queries/q.json'
            write_json(path, record)
            cache = root / 'cache.json'
            write_json(cache, {'r3': {'resolved_url': url}})
            result, audit = reconcile_pairs(pairs, articles, root, cache)
            self.assertEqual(result[0]['n_cited'], '2')  # two chunks in one trial count once
            self.assertEqual(result[0]['n_unknown_matches'], '0')
            self.assertAlmostEqual(float(result[0]['citation_proportion']), 2/3)
            self.assertEqual(result[0]['original_n_cited'], '0')
            self.assertEqual(result[0]['duplicate_pair_of'], '')
            self.assertEqual(result[1]['duplicate_pair_of'], 'p1')
            self.assertEqual(audit['confirmed_duplicate_pairs'], 1)
            self.assertEqual(audit['used_recovery_evidence'], {'r3': {'resolved_url': url}})
            self.assertEqual(len(audit['recovery_cache_sha256']), 64)
            self.assertEqual(pairs, saved)
            self.assertEqual(__import__('json').loads(path.read_text()), record)

    def test_unresolved_source_stays_unknown_not_negative(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            url = 'https://example.com/a'
            a = article('a', url, url)
            pair = {'source_batch': 'main_test', 'query_id': 'q', 'n_valid': '2', 'n_cited': '0',
                    'n_unknown_matches': '1', 'citation_proportion': '', 'in_google_top10': 'True',
                    'in_gemini_citations': 'False', 'candidate_origin': 'google_only',
                    'pair_id': 'p', 'article_id': 'a', 'article_url': url}
            write_json(root / 'data/raw/main/main_test/queries/q.json', {
                'trials': [trial(['missing'], {}), trial(['other'], {'other': {'resolved_url': 'https://other.com/a'}})]})
            result, _ = reconcile_pairs([pair], [a], root, root/'missing_cache.json')
            self.assertEqual(result[0]['n_cited'], '0')
            self.assertEqual(result[0]['n_unknown_matches'], '1')
            self.assertEqual(result[0]['citation_proportion'], '')

    def test_raw_trial_mismatch_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            url = 'https://example.com/a'
            pair = {'source_batch': 'main_test', 'query_id': 'q', 'n_valid': '3',
                    'in_google_top10': 'True', 'pair_id': 'p', 'article_id': 'a', 'article_url': url}
            write_json(root/'data/raw/main/main_test/queries/q.json', {'trials': []})
            with self.assertRaisesRegex(ValueError, 'Raw trials berbeda'):
                reconcile_pairs([pair], [article('a',url,url)], root, root/'cache.json')

    def test_known_google_destination_survives_raw_link_difference_and_failed_crawl(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            url = 'https://example.com/a'
            a = article('a', url, url)
            a.update(crawl_status='network_error', article_eligible=False, text='')
            pair = {'source_batch': 'main_test', 'query_id': 'q', 'n_valid': '2',
                    'in_google_top10': 'True', 'in_gemini_citations': 'False',
                    'candidate_origin': 'google_only', 'pair_id': 'p', 'article_id': 'a', 'article_url': url}
            saved_trial = trial(['cited'], {'cited': {'resolved_url': 'https://other.com/a'}})
            write_json(root/'data/raw/main/main_test/queries/q.json', {
                'google': {'url_resolutions': {'https://redirect.example/old': {'resolved_url': url}}},
                'trials': [saved_trial, saved_trial]})
            result, _ = reconcile_pairs([pair], [a], root, root/'cache.json')
            self.assertEqual(result[0]['n_unknown_matches'], '0')
            self.assertEqual(result[0]['citation_proportion'], '0.0')

    def test_google_redirect_identity_does_not_require_publisher_download(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.status_code = 302
        response.headers = {'Location': 'https://publisher.example/article'}
        session = MagicMock()
        session.__enter__.return_value = session
        session.request.return_value = response
        with patch('requests.Session', return_value=session), patch('pilot_gemini_grounding.validate_public_url'):
            result = resolve_url('https://vertexaisearch.cloud.google.com/grounding-api-redirect/test')
        self.assertEqual(result['resolved_url'], 'https://publisher.example/article')
        self.assertEqual(result['resolution_status'], 'destination_redirect_observed')
        self.assertEqual(session.request.call_count, 1)


if __name__ == '__main__':
    unittest.main()
