import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from article_dates import parse_publication_date, publication_details
from article_features import _metadata
from bs4 import BeautifulSoup


class PublicationDateTests(unittest.TestCase):
    def test_observed_formats_and_indonesian_timezone(self):
        for value, expected in [
            ('June 28, 2026', '2026-06-28T00:00:00'),
            ('2025-08-25T06.35.53+00:00', '2025-08-25T06:35:53+00:00'),
            ('20220102T170000Z', '2022-01-02T17:00:00+00:00'),
            ('Selasa, 18 Mei 2021 | 10.30 WIB', '2021-05-18T10:30:00+07:00'),
            ('Diterbitkan pada 2 Desember 2025', '2025-12-02T00:00:00'),
        ]:
            with self.subTest(value=value):
                self.assertEqual(parse_publication_date(value).isoformat(), expected)

    def test_does_not_invent_missing_date_parts_or_guess_ambiguous_dates(self):
        for value in ['', '2025', '2025-08', 'August 2025', '02/03/2025',
                      'Copyright 2025', 'Updated 2 May 2025', '31 February 2025']:
            self.assertIsNone(parse_publication_date(value), value)

    def test_missing_invalid_and_future_are_distinct(self):
        for value, status in [('', 'missing_publication_date'), ('n/a', 'unparseable_publication_date'),
                              ('2027-01-01', 'future_publication_date')]:
            result = publication_details(value, '2026-09-20T00:00:00Z')
            self.assertEqual(result['publication_age_status'], status)
            self.assertIsNone(result['publication_age_days'])
        result = publication_details('19 September 2026', '2026-09-20T00:00:00Z')
        self.assertEqual(result['publication_age_days'], 1)
        self.assertTrue(result['publication_timezone_assumed'])
        self.assertEqual(publication_details('2025-01-01', '')['publication_age_status'], 'invalid_retrieval_date')

    def metadata(self, html):
        return _metadata(BeautifulSoup(html, 'html.parser'), 'https://example.com/article')

    def test_fallback_keeps_source_and_ignores_related_updated_and_copyright(self):
        html = '<article><time class="published" datetime="2025-05-02"></time></article><aside><time class="published">2026-01-01</time></aside>'
        result = self.metadata(html)
        self.assertEqual(result['published_at'], '2025-05-02')
        self.assertEqual(result['published_at_source'], 'dom:time.published')
        for html in ['<meta property="article:modified_time" content="2025-05-02">',
                     '<footer>Copyright 2025</footer>',
                     '<div class="related-posts"><time class="published">2025-05-02</time></div>',
                     '<time class="entry-date updated">2025-05-02</time>',
                     '<time class="published">2025-05-02</time><time class="published">2025-05-03</time>']:
            self.assertEqual(self.metadata(html)['published_at'], '')

    def test_valid_fallback_over_invalid_metadata(self):
        result = self.metadata('<meta property="article:published_time" content="bad"><time itemprop="datePublished" datetime="2025-05-02"></time>')
        self.assertEqual(result['published_at'], '2025-05-02')
        self.assertEqual(result['published_at_source'], 'itemprop:datePublished')


if __name__ == '__main__':
    unittest.main()
