import sys
import unittest
import tempfile
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from build_article_dataset import label_for, publication_age, dataset_group, export_datasets, build
from collect_paa import write_json, write_csv, read_json
from collect_main_dataset import read_rows
from article_features import extract_features, bm25_scores
import scrape_articles


class DatasetTests(unittest.TestCase):
    def pair(self, **changes):
        return {'grounding_eligible': 'True', 'within_time_window': 'True',
                'n_valid': '2', 'n_unknown_matches': '0', 'citation_proportion': '0.5', **changes}

    def test_user_threshold_includes_one_of_two_but_not_one_of_three(self):
        self.assertEqual(label_for(self.pair(), .5), (1, 'exact'))
        self.assertEqual(label_for(self.pair(n_valid='3', citation_proportion=str(1/3)), .5), (0, 'exact'))

    def test_missing_grounding_or_unresolved_url_never_becomes_negative(self):
        self.assertIsNone(label_for(self.pair(n_valid='1'), .5)[0])
        self.assertIsNone(label_for(self.pair(n_unknown_matches='1', citation_proportion=''), .5)[0])
        self.assertIsNone(label_for(self.pair(), None)[0])

    def test_split_is_per_query_and_overlap_stays_in_primary(self):
        shared = {'article_id': 'same_url', 'in_gemini_citations': 'True'}
        self.assertEqual(dataset_group({**shared, 'query_id': 'a', 'in_google_top10': 'True',
                                        'candidate_origin': 'google_and_gemini'}), 'google_top10')
        self.assertEqual(dataset_group({**shared, 'query_id': 'b', 'in_google_top10': 'False',
                                        'candidate_origin': 'gemini_only'}), 'gemini_only')
        self.assertEqual(dataset_group({'in_google_top10': 'True', 'in_gemini_citations': 'False',
                                        'candidate_origin': 'google_only'}), 'google_top10')
        with self.assertRaises(ValueError):
            dataset_group({'in_google_top10': 'False', 'in_gemini_citations': 'True',
                           'candidate_origin': 'google_and_gemini'})
        with self.assertRaises(ValueError):
            dataset_group({'candidate_origin': 'gemini_only'})

    def test_export_preserves_uncertain_and_failed_rows_but_excludes_supplement_from_training(self):
        rows = [
            {'pair_id': 'positive', 'dataset_group': 'google_top10', 'citation_label': 1,
             'crawl_status': 'success', 'ready_for_model': True},
            {'pair_id': 'uncertain', 'dataset_group': 'google_top10', 'citation_label': None,
             'crawl_status': 'success', 'ready_for_model': False},
            {'pair_id': 'failed', 'dataset_group': 'google_top10', 'citation_label': 0,
             'crawl_status': 'robots_unavailable', 'ready_for_model': False},
            {'pair_id': 'supplement', 'dataset_group': 'gemini_only', 'citation_label': 0,
             'crawl_status': 'success', 'ready_for_model': True},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            export_datasets(path, rows, list(rows[0]), ['pair_id', 'citation_label'])
            self.assertEqual(len(read_rows(path / 'dataset_union.csv')), 4)
            primary = read_rows(path / 'dataset.csv')
            self.assertEqual([r['pair_id'] for r in primary], ['positive', 'uncertain', 'failed'])
            self.assertEqual(primary[1]['citation_label'], '')
            self.assertEqual(read_rows(path / 'dataset_gemini_only.csv')[0]['pair_id'], 'supplement')
            self.assertEqual([r['pair_id'] for r in read_rows(path / 'model_ready.csv')], ['positive'])
            # An empty supplement still produces a CSV with headers.
            export_datasets(path, rows[:3], list(rows[0]), ['pair_id', 'citation_label'])
            self.assertEqual(read_rows(path / 'dataset_gemini_only.csv'), [])

    def test_supplement_does_not_change_primary_bm25_statistics(self):
        reference = ['campak gejala anak', 'vaksin anak sehat']
        before = bm25_scores('campak anak', reference)
        after = bm25_scores('campak anak', reference + ['campak ' * 200], reference_documents=reference)
        self.assertEqual(before, after[:2])
        self.assertEqual(bm25_scores('asing', ['asing'], reference_documents=reference), [0.0])
        with self.assertRaises(ValueError):
            bm25_scores('campak', ['campak'], reference_documents=[])

    def test_resume_scraping_routes_new_pairs_without_refetching_old_or_training_on_supplement(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            crawl = {'dataset_id': 'articles_future', 'source_batches': ['main_future']}
            config = {'scrape_config': 'configs/crawl.json', 'credibility_csv': 'data/manual/credibility.csv',
                      'article_review_csv': 'data/manual/review.csv', 'citation_threshold': .5,
                      'bm25_k1': 1.5, 'bm25_b': .75, 'feature_version': 'test'}
            write_json(root / config['scrape_config'], crawl)
            source = []
            for pair_id, article_id, origin, proportion in [
                ('p1', 'article_1', 'google_and_gemini', '0.5'),
                ('p2', 'article_1', 'gemini_only', '0.5'),
                ('p3', 'article_2', 'google_only', '0'),
                ('p4', 'article_3', 'gemini_only', '0.5'),
            ]:
                source.append({**self.pair(), 'pair_id': pair_id, 'query_id': 'query_' + pair_id,
                               'query_text': 'Pertanyaan ' + pair_id, 'domain': 'kesehatan',
                               'article_id': article_id, 'article_url': f'https://{article_id.replace("_", "")}.example/article',
                               'candidate_origin': origin, 'in_google_top10': origin != 'gemini_only',
                               'in_gemini_citations': origin != 'google_only',
                               'collection_complete': True, 'citation_proportion': proportion})
            write_csv(root / 'data/interim/main/main_future/query_article_pairs_union.csv', source, list(source[0]))
            write_csv(root / config['credibility_csv'], [
                {'hostname': f'article{i}.example', 'credibility_level': '2', 'review_status': 'verified'}
                for i in range(1, 4)], ['hostname', 'credibility_level', 'review_status'])
            manifest = scrape_articles.make_manifest(crawl, root)
            calls = []

            def fetch(url):
                calls.append(url)
                if 'article3.example' in url:
                    return {'status': 'robots_unavailable', 'final_url': url, 'body': b''}
                return {'status': 'success', 'http_status': 200, 'final_url': url,
                        'content_type': 'text/html', 'body': b'<html><article>Test</article></html>'}

            def extract(*args, **kwargs):
                return {'title': 'Judul', 'text': 'Isi artikel kesehatan untuk pertanyaan.',
                        'language': 'id', 'article_review_status': 'eligible_auto', 'word_count': 6}

            with patch('build_article_dataset.LocalEmbeddings') as embeddings:
                embeddings.return_value.vector.return_value = (np.array([1., 0.]), {'n_chunks': 1})
                embeddings.return_value.fingerprint.return_value = {'test': True}
                scrape_articles.collect(manifest, root, max_new_urls=1, fetcher=fetch, extractor=extract)
                first = build(config, root, with_embeddings=True, reextract=False)
                checkpoints = root / 'data/raw/articles/articles_future/records'
                saved = {p.name: p.read_bytes() for p in checkpoints.glob('*.json')}
                scrape_articles.collect(manifest, root, max_new_urls=2, fetcher=fetch, extractor=extract)
                result = build(config, root, with_embeddings=True, reextract=False)
                self.assertTrue({r['pair_id'] for r in first} <= {r['pair_id'] for r in result})
                self.assertEqual(len(calls), 3)
                self.assertEqual(len(set(calls)), 3)  # Shared URL for p1/p2 is fetched just once.
                for name, content in saved.items():
                    self.assertEqual((checkpoints / name).read_bytes(), content)
                output = root / 'data/processed/articles_future'
                self.assertEqual({r['pair_id'] for r in read_rows(output / 'dataset.csv')}, {'p1', 'p3'})
                supplement = read_rows(output / 'dataset_gemini_only.csv')
                self.assertEqual({r['pair_id'] for r in supplement}, {'p2', 'p4'})
                self.assertEqual(next(r for r in supplement if r['pair_id'] == 'p4')['crawl_status'], 'robots_unavailable')
                self.assertEqual({r['pair_id'] for r in read_rows(output / 'model_ready.csv')}, {'p1', 'p3'})
                self.assertEqual(read_json(output / 'summary.json')['attempted_urls'], 3)
                # Rebuilding locally cannot add pairs or require another fetch.
                again = build(config, root, with_embeddings=True, reextract=False)
                self.assertEqual(len(again), 4)
                self.assertEqual(len(calls), 3)

    def test_invalid_future_and_unknown_publication_dates_remain_missing(self):
        self.assertIsNone(publication_age('not a date', '2026-09-12T00:00:00Z'))
        self.assertIsNone(publication_age('2027-01-01', '2026-09-12T00:00:00Z'))
        self.assertEqual(publication_age('2026-09-11', '2026-09-12T00:00:00Z'), 1)

    def test_pegadaian_body_excludes_related_articles(self):
        body = 'Penjelasan barang yang dapat digadaikan beserta persyaratan layanan untuk nasabah. ' * 15
        html = '<html lang="id"><h1>Barang gadai</h1><div id="default"><span class="default-content"><p>'+body+'</p></span></div><p>IKLAN TERKAIT DI LUAR BADAN</p></html>'
        result = extract_features(html, 'https://pegadaian.co.id/artikel/test')
        self.assertIn('persyaratan', result['text'])
        self.assertNotIn('IKLAN TERKAIT', result['text'])

    def test_kemenkes_full_expandable_text_is_used_instead_of_teaser(self):
        html = '<html lang="id"><h1>Campak</h1><div id="isi-kecil">RINGKASAN</div><div id="isi-lengkap"><p>' + ('Penyakit campak memiliki gejala yang perlu dipahami untuk menjaga kesehatan anak. ' * 12) + '</p></div></html>'
        result = extract_features(html, 'https://ayosehat.kemkes.go.id/topik/campak')
        self.assertNotIn('RINGKASAN', result['text'])
        self.assertGreater(result['word_count'], 100)


if __name__ == '__main__':
    unittest.main()
