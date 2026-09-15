"""Offline extraction regression tests: real failure modes, no network/API use."""

import json
import math
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from article_features import bm25_scores, extract_features, tokenize


TEXT = ('Kesehatan tubuh dapat dijaga dengan makanan bergizi serta istirahat yang cukup. '
        'Dokter menjelaskan bahwa pemeriksaan secara teratur membantu mengetahui kondisi kesehatan. ')


def article(body, metadata='', language='id'):
    schema = {'@context': 'https://schema.org', '@type': 'NewsArticle', 'headline': 'Contoh artikel',
              'author': [{'@type': 'Person', 'name': 'Penulis Contoh'}], 'datePublished': '2026-09-11'}
    return f'''<html lang="{language}"><head><script type="application/ld+json">{json.dumps(schema)}</script>
    {metadata}</head><body><nav><h1>Navigasi palsu</h1><ul><li>Menu</li></ul></nav>
    <article>{body}</article><footer><p>Informasi footer 99%</p></footer></body></html>'''


class ArticleFeatureTests(unittest.TestCase):
    def test_counts_are_from_clean_body_and_keep_links_metadata(self):
        result = extract_features(article(
            '<h1>Judul artikel</h1><h2>Penyebab</h2>'
            '<p>' + TEXT * 6 + '</p><p>Hasil penelitian tercatat sebesar 20 persen.</p>'
            '<ul><li>Makanan sehat</li><li>Istirahat cukup</li></ul>'
            '<blockquote>"Penjelasan dokter dapat diperiksa."</blockquote>'
            '<p><a href="https://evidence.example/studi">Sumber</a>'
            '<a href="/lainnya">Internal</a></p>'
            '<aside><h2>Terkait</h2><p>IKLAN 90%</p></aside>'
            '<div class="related-articles"><p>TERKAIT PALSU</p></div>',
            '<link rel="canonical" href="/artikel-kanonis">'), 'https://website.example/artikel')
        self.assertEqual(result['extraction_method'], 'dom:article')
        self.assertNotIn('Navigasi palsu', result['text'])
        self.assertNotIn('IKLAN', result['text'])
        self.assertNotIn('TERKAIT PALSU', result['text'])
        self.assertEqual(result['h1_count'], 1)
        self.assertEqual(result['h2_count'], 1)
        self.assertEqual(result['list_count'], 1)
        self.assertEqual(result['list_item_count'], 2)
        self.assertEqual(result['statistic_mention_count'], 1)
        self.assertEqual(result['blockquote_count'], 1)
        self.assertEqual(result['external_reference_count'], 1)
        self.assertEqual(result['author'], 'Penulis Contoh')
        self.assertEqual(result['canonical_url'], 'https://website.example/artikel-kanonis')
        self.assertEqual(result['article_review_status'], 'eligible_auto')
        self.assertAlmostEqual(result['wps'], result['word_count'] / result['sentence_count'])
        self.assertAlmostEqual(result['cpw'], result['char_count'] / result['word_count'])
        json.dumps(result)

    def test_publisher_body_selector_ignores_article_wrapper_related_sections(self):
        body = '<div class="detail__body-text"><p>' + TEXT * 6 + '</p></div><p>RELATED OUTSIDE BODY</p>'
        result = extract_features(article(body), 'https://news.example/read/123')
        self.assertEqual(result['extraction_method'], 'dom:.detail__body-text')
        self.assertNotIn('RELATED OUTSIDE BODY', result['text'])

    def test_long_homepage_is_not_accepted_as_article(self):
        result = extract_features(article('<p>' + TEXT * 6 + '</p>'), 'https://example.com/')
        self.assertFalse(result['article_eligible'])
        self.assertEqual(result['article_review_status'], 'not_article')

    def test_short_or_empty_extraction_has_explicit_review_status(self):
        with patch('trafilatura.extract', return_value=None):
            short = extract_features(article('<p>Informasi singkat.</p>'), 'https://example.com/short')
            empty = extract_features('<html><body></body></html>', 'https://example.com/empty')
        self.assertEqual(short['article_review_status'], 'too_short')
        self.assertEqual(empty['article_review_status'], 'extraction_empty')
        self.assertIsNone(empty['wps'])
        self.assertIsNone(empty['cpw'])

    def test_language_conflict_requires_review_and_is_deterministic(self):
        html = article('<p>' + TEXT * 6 + '</p>', language='en')
        result = extract_features(html, 'https://example.com/article')
        again = extract_features(html, 'https://example.com/article')
        self.assertEqual(result['language_detected'], 'id')
        self.assertEqual(result['article_review_status'], 'needs_language_review')
        self.assertEqual(result, again)

    def test_malformed_jsonld_does_not_discard_visible_content(self):
        html = '<html lang="id"><head><title>Judul</title><script type="application/ld+json">{broken</script></head><body>'
        html += '<article><p>' + TEXT * 6 + '</p></article></body></html>'
        result = extract_features(html, 'https://example.com/artikel')
        self.assertGreater(result['word_count'], 100)
        self.assertEqual(result['article_review_status'], 'needs_page_type_review')
        self.assertFalse(result['has_author'])

    def test_product_schema_is_marked_non_article_even_with_long_description(self):
        html = '<html lang="id"><head><title>Produk</title><script type="application/ld+json">'
        html += '{"@type":"Product","name":"Produk"}</script></head><body>'
        html += '<div class="entry-content"><p>' + TEXT * 6 + '</p></div></body></html>'
        result = extract_features(html, 'https://example.com/produk')
        self.assertEqual(result['article_review_status'], 'not_article')
        self.assertFalse(result['article_eligible'])

    def test_malformed_link_does_not_lose_article(self):
        html = article('<p>' + TEXT * 6 + '</p><a href="https://[broken">Rusak</a>',
                       '<link rel="canonical" href="https://[broken">')
        result = extract_features(html, 'https://example.com/artikel')
        self.assertGreater(result['word_count'], 100)
        self.assertEqual(result['canonical_url'], '')
        self.assertEqual(result['external_reference_count'], 0)


class BM25Tests(unittest.TestCase):
    def test_corpus_idf_and_length_normalization_match_hand_calculation(self):
        # N=3, df(bank)=2, avgdl=2. Query repetition must not change score.
        documents = ['bank bank deposito', 'bank', 'vitamin sehat']
        scores = bm25_scores('BANK', documents)
        idf = math.log1p(1.5 / 2.5)
        self.assertAlmostEqual(scores[0], idf * 2 * 2.5 / (2 + 1.5 * (.25 + .75 * 3 / 2)))
        self.assertAlmostEqual(scores[1], idf * 2.5 / (1 + 1.5 * (.25 + .75 / 2)))
        self.assertEqual(scores[2], 0)
        self.assertEqual(scores, bm25_scores('bank bank', documents))

    def test_empty_corpus_unseen_terms_and_unicode_normalization(self):
        self.assertEqual(bm25_scores('bank', []), [])
        self.assertEqual(bm25_scores('bank', ['', '']), [0, 0])
        self.assertEqual(bm25_scores('kesehatan', ['bank']), [0])
        self.assertEqual(tokenize('ＢＡＮＫ café'), ['bank', 'café'])
        with self.assertRaises(ValueError):
            bm25_scores('bank', ['bank'], b=2)


if __name__ == '__main__':
    unittest.main()
