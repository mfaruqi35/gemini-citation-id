"""Reproducible article extraction and surface features (protocol version 1).

Features describe presentation, not factual correctness. ``char_count`` counts
Unicode letters/digits in normalized body tokens (spaces/punctuation excluded).
WPS = body tokens / heuristic sentence count; CPW = char_count / body tokens.
Sentences split on end punctuation followed by whitespace, or paragraph breaks;
abbreviations are not resolved. Number/statistic/quote matches are surface cues.
Structural counts refer to the cleaned article subtree, including its headings;
``extraction_method`` identifies DOM selectors versus reconstructed fallback HTML.
Dates are publisher-declared strings, never inferred from retrieval time.

BM25 uses NFKC + casefold Unicode word tokens, no stemming/stopwords, unique query
terms, k1=1.5, b=.75, and positive Robertson IDF log(1+(N-df+.5)/(df+.5)).
Caller supplies the entire frozen corpus, not a different corpus per query.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
from bs4.element import Tag


FEATURE_VERSION = 1
MODEL_FEATURE_FIELDS = [
    'word_count', 'sentence_count', 'char_count', 'paragraph_count',
    'heading_count', 'section_heading_count',
    'h1_count', 'h2_count', 'h3_count', 'h4_count', 'h5_count', 'h6_count',
    'list_count', 'list_item_count', 'table_count', 'image_count',
    'mean_paragraph_word_count', 'paragraphs_per_100_words', 'wps', 'cpw',
    'numeric_mention_count', 'has_numeric_mention',
    'statistic_mention_count', 'has_statistic_mention',
    'blockquote_count', 'quote_span_count', 'has_quote',
    'external_reference_count', 'external_reference_unique_count', 'has_external_reference',
    'has_author', 'has_published_at', 'has_modified_at',
]
WORD_RE = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*", re.UNICODE)
ARTICLE_TYPES = {
    'Article', 'NewsArticle', 'BlogPosting', 'MedicalScholarlyArticle',
    'ScholarlyArticle', 'TechArticle', 'Report', 'AnalysisNewsArticle',
    'OpinionNewsArticle', 'AdvertiserContentArticle', 'ReviewNewsArticle',
}
NON_ARTICLE_TYPES = {'Product', 'SoftwareApplication', 'MobileApplication', 'QAPage', 'DiscussionForumPosting', 'SearchResultsPage', 'CollectionPage', 'VideoObject'}
SITE_BODY_SELECTORS = {
    # Inspected against saved HTML from the first 20-URL run, 2026-09-12.
    'pegadaian.co.id': '#default .default-content',
    'kapzconsulting.com': '.post_text_inner',
    'dqlab.id': '#content-desc',
    'support.google.com': '.article-content-container .cc',
    'ekahospital.com': '.grow .content',
    'pajak.go.id': 'article',
    'ayosehat.kemkes.go.id': '#isi-lengkap',
}
BODY_SELECTORS = (
    '[itemprop="articleBody"]', '.detail__body-text', '.read__content',
    '.article__body', '.article-body', '.article__content', '.article-content',
    '#article-content', '.entry-content', '.post-content', '.td-post-content',
    '.content-article', '.detail-content', '.single-content',
)
JUNK_SELECTORS = (
    'script', 'style', 'noscript', 'nav', 'footer', 'aside', 'form', 'button',
    '[hidden]', '[aria-hidden="true"]', '.ads', '.advertisement', '.ad-slot',
    '.related', '.related-articles', '.related-posts', '.baca-juga', '.read-also',
    '.share', '.social-share', '.comments', '#comments', '.breadcrumb',
    '.pagination', '.cookie-banner', '.newsletter', '.post_info', '.entry_title', '.field__label',
)


def tokenize(text: str) -> list[str]:
    """Same tokenizer for body lengths, BM25 documents, and query text."""
    return WORD_RE.findall(unicodedata.normalize('NFKC', text).casefold())


def bm25_scores(query: str, documents: list[str], k1: float = 1.5, b: float = .75,
                reference_documents: list[str] | None = None) -> list[float]:
    """Score documents using a fixed reference corpus (by default the documents)."""
    if k1 <= 0 or not 0 <= b <= 1:
        raise ValueError('BM25 requires k1 > 0 and 0 <= b <= 1')
    if not documents:
        return []
    counts = [Counter(tokenize(document)) for document in documents]
    lengths = [sum(counter.values()) for counter in counts]
    reference = counts if reference_documents is None else [Counter(tokenize(d)) for d in reference_documents]
    if not reference:
        raise ValueError('BM25 reference corpus is empty.')
    average = sum(sum(counter.values()) for counter in reference) / len(reference)
    if not average:
        return [0.0] * len(documents)
    terms = sorted(set(tokenize(query)))
    frequencies = {term: sum(term in counter for counter in reference) for term in terms}
    result = []
    for counter, length in zip(counts, lengths):
        score = 0.0
        for term in terms:
            frequency = counter[term]
            if frequency and frequencies[term]:
                idf = math.log1p((len(reference) - frequencies[term] + .5) / (frequencies[term] + .5))
                denominator = frequency + k1 * (1 - b + b * length / average)
                score += idf * frequency * (k1 + 1) / denominator
        result.append(score)
    return result


def _normal(text) -> str:
    return re.sub(r'\s+', ' ', str(text or '')).strip()


def _schema_nodes(value):
    if isinstance(value, list):
        for child in value:
            yield from _schema_nodes(child)
    elif isinstance(value, dict):
        yield value
        for key in ('@graph', 'mainEntity'):
            yield from _schema_nodes(value.get(key))


def _types(node: dict) -> set[str]:
    values = node.get('@type', [])
    values = values if isinstance(values, list) else [values]
    return {str(value).rsplit('/', 1)[-1] for value in values}


def _author(value) -> str:
    if isinstance(value, list):
        return '; '.join(filter(None, (_author(item) for item in value)))
    if isinstance(value, dict):
        return _normal(value.get('name', ''))
    return _normal(value)


def _metadata(soup: BeautifulSoup, url: str) -> dict:
    def meta(*names):
        for name in names:
            tag = soup.find('meta', attrs={'name': name}) or soup.find('meta', attrs={'property': name})
            if tag and tag.get('content'):
                return _normal(tag['content'])
        return ''

    def time_value(property_name):
        tag = soup.select_one(f'[itemprop="{property_name}"]')
        if tag is not None:
            return _normal(tag.get('content') or tag.get('datetime') or tag.get_text(' ', strip=True))
        return ''

    nodes = []
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            nodes.extend(_schema_nodes(json.loads(script.string or script.get_text())))
        except (ValueError, TypeError):
            continue
    article = next((node for node in nodes if _types(node) & ARTICLE_TYPES), {})
    all_types = set().union(*(_types(node) for node in nodes)) if nodes else set()
    title_tag = soup.find('h1') or soup.find('title')
    canonical = soup.find('link', rel='canonical')
    try:
        canonical_url = urljoin(url, canonical.get('href', '')) if canonical else ''
        if urlsplit(canonical_url).scheme not in {'http', 'https'}:
            canonical_url = ''
    except ValueError:
        canonical_url = ''
    html_tag = soup.find('html')
    declared = (html_tag.get('lang', '') if html_tag else '') or meta('og:locale', 'language') or article.get('inLanguage', '')
    declared = str(declared).replace('_', '-').lower().split('-')[0]
    byline = soup.select_one('[rel="author"], [itemprop="author"]')
    return {
        'title': _normal(article.get('headline')) or (title_tag.get_text(' ', strip=True) if soup.find('h1') else '') or meta('og:title', 'twitter:title') or (title_tag.get_text(' ', strip=True) if title_tag else ''),
        'author': _author(article.get('author')) or meta('author', 'article:author') or (byline.get_text(' ', strip=True) if byline else ''),
        'published_at': _normal(article.get('datePublished')) or meta('article:published_time', 'datePublished', 'pubdate', 'publishdate') or time_value('datePublished'),
        'modified_at': _normal(article.get('dateModified')) or meta('article:modified_time', 'dateModified', 'lastmod') or time_value('dateModified'),
        'canonical_url': canonical_url,
        'language_declared': {'in': 'id'}.get(declared, declared),
        'schema_types': sorted(all_types),
        'has_article_schema': bool(article),
        'open_graph_type': meta('og:type'),
    }


def _clean(node: Tag) -> BeautifulSoup:
    cleaned = BeautifulSoup(str(node), 'html.parser')
    for tag in list(cleaned.select(','.join(JUNK_SELECTORS))):
        # An ancestor may already have been removed.
        if tag.parent is not None:
            tag.decompose()
    return cleaned


def _body(soup: BeautifulSoup, html: str, url: str) -> tuple[BeautifulSoup, str]:
    host = (urlsplit(url).hostname or '').removeprefix('www.')
    selector = SITE_BODY_SELECTORS.get(host)
    if selector:
        matches = [_clean(tag) for tag in soup.select(selector)]
        if matches:
            best = max(matches, key=lambda node: len(tokenize(node.get_text(' ', strip=True))))
            if len(tokenize(best.get_text(' ', strip=True))) >= 20:
                return best, 'dom:site:' + selector
    for selector in BODY_SELECTORS:
        matches = [_clean(tag) for tag in soup.select(selector)]
        if matches:
            best = max(matches, key=lambda node: len(tokenize(node.get_text(' ', strip=True))))
            if len(tokenize(best.get_text(' ', strip=True))) >= 20:
                return best, 'dom:' + selector
    articles = [_clean(tag) for tag in soup.find_all('article')]
    if articles:
        best = max(articles, key=lambda node: len(tokenize(node.get_text(' ', strip=True))))
        if len(tokenize(best.get_text(' ', strip=True))) >= 20:
            return best, 'dom:article'

    # Fallback reconstructs a content-only DOM and preserves headings/lists/links
    # supported by Trafilatura. Its provenance differs from an exact DOM selector.
    import trafilatura
    extracted = trafilatura.extract(
        html, url=url, output_format='html', include_comments=False,
        include_tables=True, include_links=True, include_formatting=True,
        favor_precision=True, deduplicate=False,
    )
    if extracted:
        return _clean(BeautifulSoup(extracted, 'html.parser')), 'trafilatura:html'
    # Keep short visible text for audit; never classify this whole-page fallback
    # as a verified article merely because it contains many navigation words.
    return _clean(soup.find('main') or soup.find('body') or soup), 'dom:unconfirmed_fallback'


def _body_text(body: BeautifulSoup) -> str:
    text_tree = BeautifulSoup(str(body), 'html.parser')
    for tag in text_tree.select('p,h1,h2,h3,h4,h5,h6,li,blockquote,table,div,section,br'):
        tag.insert_before('\n')
        tag.insert_after('\n')
    return '\n'.join(line for line in (_normal(line) for line in text_tree.get_text(' ').splitlines()) if line)


def _language(text: str, declared: str) -> dict:
    from langdetect import DetectorFactory, detect_langs
    from langdetect.lang_detect_exception import LangDetectException
    DetectorFactory.seed = 0
    detected, confidence = '', None
    if len(tokenize(text)) >= 20:
        try:
            result = detect_langs(text[:20000])[0]
            detected, confidence = result.lang, result.prob
        except LangDetectException:
            pass
    language = detected if confidence is not None and confidence >= .90 else declared
    conflict = bool(declared and detected and declared != detected and confidence is not None and confidence >= .90)
    return {
        'language': language, 'language_detected': detected,
        'language_confidence': confidence, 'language_metadata_conflict': conflict,
    }


def extract_features(html: str, url: str, min_words: int = 100) -> dict:
    """Extract metadata/body/features without fetching URLs or making API calls.

    ``eligible_auto`` means passed machine screening, not human verification or
    model readiness. Unknown/conflicting language or page type remains reviewable.
    Canonical links are evidence only: this function never merges article IDs.
    """
    if min_words < 1:
        raise ValueError('min_words must be positive')
    soup = BeautifulSoup(html, 'html.parser')
    metadata = _metadata(soup, url)
    body, method = _body(soup, html, url)
    text = _body_text(body)
    tokens = tokenize(text)
    paragraphs = [tag.get_text(' ', strip=True) for tag in body.find_all('p') if tag.get_text(' ', strip=True)]
    headings = [{'level': int(tag.name[1]), 'text': tag.get_text(' ', strip=True)} for tag in body.find_all(re.compile(r'^h[1-6]$')) if tag.get_text(' ', strip=True)]
    sentence_count = len([part for part in re.split(r'(?<=[.!?])\s+|\n+', text) if tokenize(part)])
    character_count = sum(sum(character.isalnum() for character in token) for token in tokens)
    external_links = []
    host = (urlsplit(url).hostname or '').lower().removeprefix('www.')
    for anchor in body.find_all('a', href=True):
        try:
            target = urljoin(url, anchor['href'])
            target_host = (urlsplit(target).hostname or '').lower().removeprefix('www.')
        except ValueError:
            continue
        if urlsplit(target).scheme in {'http', 'https'} and target_host and target_host != host:
            external_links.append({'url': target, 'text': anchor.get_text(' ', strip=True)})

    # Body links are reference candidates, not verified supporting evidence.
    schema_types = set(metadata['schema_types'])
    path = urlsplit(url).path.rstrip('/')
    if not path:
        page_type = 'homepage'
    elif metadata['has_article_schema'] or metadata['open_graph_type'] == 'article':
        page_type = 'article'
    elif schema_types & NON_ARTICLE_TYPES:
        page_type = 'non_article'
    elif method == 'dom:article' or (method.startswith('dom:') and method != 'dom:unconfirmed_fallback' and paragraphs and metadata['title']):
        page_type = 'article_candidate'
    else:
        page_type = 'unknown'
    language = _language(text, metadata['language_declared'])
    if not tokens:
        status = 'extraction_empty'
    elif page_type in {'homepage', 'non_article'}:
        status = 'not_article'
    elif len(tokens) < min_words:
        status = 'too_short'
    elif language['language_metadata_conflict']:
        status = 'needs_language_review'
    elif language['language'] and language['language'] != 'id':
        status = 'non_indonesian'
    elif language['language'] != 'id':
        status = 'needs_language_review'
    elif page_type != 'article' or method == 'dom:unconfirmed_fallback':
        status = 'needs_page_type_review'
    else:
        status = 'eligible_auto'

    numeric_count = len(re.findall(r'(?<!\w)\d+(?:[.,]\d+)*(?!\w)', text))
    statistic_count = len(re.findall(r'\d+(?:[.,]\d+)*\s*(?:%|persen\b|persentase\b)', text, re.I))
    quote_count = len(re.findall(r'"[^"\n]{5,}"|“[^”\n]{5,}”', text))
    paragraph_words = sum(len(tokenize(paragraph)) for paragraph in paragraphs)
    result = {
        **metadata, **language,
        'feature_version': FEATURE_VERSION, 'extraction_method': method,
        'text': text, 'paragraphs': paragraphs, 'headings': headings,
        'page_type': page_type, 'article_review_status': status,
        'article_eligible': status == 'eligible_auto', 'min_words': min_words,
        'word_count': len(tokens), 'sentence_count': sentence_count,
        'char_count': character_count, 'paragraph_count': len(paragraphs),
        'heading_count': len(headings), 'section_heading_count': sum(item['level'] >= 2 for item in headings),
        'list_count': len(body.find_all(['ul', 'ol'])), 'list_item_count': len(body.find_all('li')),
        'table_count': len(body.find_all('table')), 'image_count': len(body.find_all('img')),
        'mean_paragraph_word_count': paragraph_words / len(paragraphs) if paragraphs else None,
        'paragraphs_per_100_words': 100 * len(paragraphs) / len(tokens) if tokens else None,
        'wps': len(tokens) / sentence_count if sentence_count else None,
        'cpw': character_count / len(tokens) if tokens else None,
        'numeric_mention_count': numeric_count, 'has_numeric_mention': bool(numeric_count),
        'statistic_mention_count': statistic_count, 'has_statistic_mention': bool(statistic_count),
        'blockquote_count': len(body.find_all('blockquote')), 'quote_span_count': quote_count,
        'has_quote': bool(quote_count or body.find('blockquote')),
        'external_reference_count': len(external_links),
        'external_reference_unique_count': len({item['url'] for item in external_links}),
        'has_external_reference': bool(external_links), 'external_links': external_links,
        'has_author': bool(metadata['author']),
        'has_published_at': bool(metadata['published_at']), 'has_modified_at': bool(metadata['modified_at']),
    }
    for level in range(1, 7):
        result[f'h{level}_count'] = sum(item['level'] == level for item in headings)
    return result
