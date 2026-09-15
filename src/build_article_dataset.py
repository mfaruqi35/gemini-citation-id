"""Export article features and query-article labels from saved crawl checkpoints."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from collect_paa import read_json, write_json, write_csv, now
from collect_main_dataset import read_rows, normalize_url
from article_features import extract_features, bm25_scores, MODEL_FEATURE_FIELDS
from article_embeddings import LocalEmbeddings

ROOT = Path(__file__).resolve().parents[1]
EXTRA_FEATURES = ['publication_age_days', 'credibility_level', 'bm25', 'semantic_cosine']
DATASET_PROTOCOL = 'google_top10_primary_gemini_only_supplement_v1'


def optional_rows(path):
    return read_rows(path) if path.exists() else []


def dataset_group(pair):
    """Membership is per query-article pair, never globally per URL."""
    flags = []
    for name in ('in_google_top10', 'in_gemini_citations'):
        value = pair.get(name)
        if value not in (True, False, 'True', 'False'):
            raise ValueError(f'Flag sumber tidak valid: {name}={value!r}')
        flags.append(value in (True, 'True'))
    google, gemini = flags
    expected_origin = 'google_and_gemini' if google and gemini else 'google_only' if google else 'gemini_only'
    if not (google or gemini) or pair.get('candidate_origin') != expected_origin:
        raise ValueError('Asal kandidat tidak konsisten dengan flag Google/Gemini.')
    return 'google_top10' if google else 'gemini_only'


def export_datasets(output, dataset, fields, model_fields):
    """Primary training candidates and supplemental observations stay separate."""
    primary = [p for p in dataset if p['dataset_group'] == 'google_top10']
    supplement = [p for p in dataset if p['dataset_group'] == 'gemini_only']
    write_csv(output / 'dataset_union.csv', dataset, fields)
    write_csv(output / 'dataset.csv', primary, fields)
    write_csv(output / 'dataset_gemini_only.csv', supplement, fields)
    ready = [{key: p.get(key) for key in model_fields} for p in primary if p['ready_for_model']]
    write_csv(output / 'model_ready.csv', ready, model_fields)
    return primary, supplement, ready


def label_for(pair, threshold):
    """Missing grounding and unresolved matches are never negative evidence."""
    if (pair.get('grounding_eligible') != 'True' or pair.get('within_time_window') != 'True'
            or int(pair.get('n_valid') or 0) < 2):
        return None, 'query_not_eligible'
    if int(pair.get('n_unknown_matches') or 0) or pair.get('citation_proportion') in ('', None):
        return None, 'url_matching_uncertain'
    if threshold is None:
        return None, 'threshold_not_set'
    if not 0 < threshold <= 1:
        raise ValueError('Ambang sitasi harus >0 dan <=1.')
    return int(float(pair['citation_proportion']) >= threshold), 'exact'


def publication_age(value, retrieved_at):
    if not value:
        return None
    try:
        from dateutil.parser import isoparse
        published = isoparse(value)
        retrieved = isoparse(retrieved_at)
        published = published.replace(tzinfo=published.tzinfo or timezone.utc)
        retrieved = retrieved.replace(tzinfo=retrieved.tzinfo or timezone.utc)
        age = (retrieved - published).total_seconds() / 86400
        return round(age, 3) if age >= 0 else None
    except (ValueError, TypeError):
        return None


def safe_path(root, name):
    path = (root / name).resolve()
    path.relative_to(root.resolve())
    return path


def build(config, root=ROOT, with_embeddings=False, reextract=True):
    crawl_config = read_json(safe_path(root, config['scrape_config']))
    dataset_id = crawl_config['dataset_id']
    raw = safe_path(root, crawl_config.get('raw_dir', f'data/raw/articles/{dataset_id}'))
    manifest = read_json(raw / 'manifest.json')
    output = root / 'data/processed' / dataset_id
    credibility = {r['hostname'].casefold(): r for r in optional_rows(root / config['credibility_csv'])}
    reviews = {r['article_id']: r for r in optional_rows(root / config['article_review_csv'])}
    records, articles = {}, []
    # Source provenance is preserved; only attempted articles enter this dataset snapshot.
    for item in manifest['articles']:
        article_id = item['article_id']
        path = raw / 'records' / (article_id + '.json')
        if not path.exists():
            continue
        record = read_json(path)
        if not record.get('attempts'):
            continue
        attempt = record['attempts'][-1]
        extraction = record.get('extraction') or {}
        derived_status = record['status']
        if reextract and record['status'] in {'success', 'extraction_error'} and attempt.get('raw_html_path'):
            from scrape_articles import decode_body
            html = decode_body(safe_path(root, attempt['raw_html_path']).read_bytes(), attempt.get('content_type', ''))
            extraction = extract_features(html, attempt.get('final_url') or item['article_url'],
                                          min_words=crawl_config.get('min_words', 100))
            derived_status = 'success'
        # Derived extraction is separately versioned; do not alter raw crawl records.
        write_json(output / 'extractions' / (article_id + '.json'), extraction)
        final_url = attempt.get('final_url') or item['article_url']
        host = (urlsplit(final_url).hostname or '').casefold()
        credibility_row = credibility.get(host, {})
        level = credibility_row.get('credibility_level', '')
        if level and level not in {'1', '2', '3', '4', '5'}:
            raise ValueError('Tingkat kredibilitas harus 1-5 atau kosong: ' + host)
        review = reviews.get(article_id, {})
        review_status = review.get('status') or extraction.get('article_review_status', 'not_extracted')
        lang = review.get('language') or extraction.get('language', '')
        eligible = (derived_status == 'success' and bool(extraction.get('text'))
                    and lang == 'id' and review_status in {'accepted', 'eligible_auto'})
        row = {
            'article_id': article_id, 'article_url': item['article_url'], 'final_url': final_url,
            'hostname': host, 'crawl_status': derived_status, 'original_crawl_status': record['status'],
            'http_status': attempt.get('http_status', ''), 'error_type': attempt.get('error_type', ''),
            'robots_status': attempt.get('robots_status', ''),
            'retrieved_at': attempt.get('finished_at') or attempt.get('started_at', ''),
            'raw_html_path': attempt.get('raw_html_path', ''),
            'title': extraction.get('title', ''), 'text': extraction.get('text', ''),
            'language': lang, 'article_review_status': review_status,
            'article_review_reason': review.get('reason', ''),
            'article_eligible': eligible, 'page_type': extraction.get('page_type', ''),
            'extraction_method': extraction.get('extraction_method', ''),
            'canonical_url': extraction.get('canonical_url', ''),
            'author': extraction.get('author', ''), 'published_at': extraction.get('published_at', ''),
            'modified_at': extraction.get('modified_at', ''),
            **{key: extraction.get(key) for key in MODEL_FEATURE_FIELDS},
            'publication_age_days': publication_age(extraction.get('published_at'),
                                                    attempt.get('finished_at') or attempt['started_at']),
            'credibility_level': int(level) if level else None,
            'credibility_status': credibility_row.get('review_status', 'not_reviewed'),
            'credibility_evidence': credibility_row.get('evidence_urls', ''),
            'credibility_reason': credibility_row.get('reason', ''),
        }
        records[article_id] = record
        articles.append(row)
    if not articles:
        raise ValueError('Belum ada URL yang dicoba. Jalankan scraper terlebih dahulu.')
    by_id = {a['article_id']: a for a in articles}
    corpus = [a for a in articles if a['article_eligible']]
    corpus_index = {a['article_id']: i for i, a in enumerate(corpus)}
    documents = [(a['title'] + '\n' + a['text']).strip() for a in corpus]
    pairs = [p for p in manifest['pairs'] if p['article_id'] in by_id]
    google_ids = {p['article_id'] for p in pairs if dataset_group(p) == 'google_top10'}
    reference = [(a['article_id'], documents[i]) for i, a in enumerate(corpus) if a['article_id'] in google_ids]
    reference_documents = [text for _, text in reference]
    corpus_hash = hashlib.sha256(json.dumps(reference, ensure_ascii=False).encode('utf-8')).hexdigest()
    bm25 = {q: (bm25_scores(q, documents, config['bm25_k1'], config['bm25_b'],
                           reference_documents=reference_documents) if reference else [None] * len(documents))
            for q in {p['query_text'] for p in pairs}}
    vectors, query_vectors, semantic_metadata = {}, {}, {}
    semantic_status = 'not_requested'
    if with_embeddings and corpus:
        engine = LocalEmbeddings(config, root)
        for article, text in zip(corpus, documents):
            print('Embedding artikel:', article['article_id'], flush=True)
            vectors[article['article_id']], semantic_metadata[article['article_id']] = engine.vector(text, 'article')
        for q in sorted({p['query_text'] for p in pairs if p['article_id'] in vectors}):
            query_vectors[q], _ = engine.vector(q, 'query')
        semantic_status = 'computed_local'
        write_json(output / 'embedding_model_manifest.json', engine.fingerprint())
    # Same canonical/final URL is an alias candidate, never an automatic relabel.
    aliases = defaultdict(set)
    for a in articles:
        for url in [a['final_url'], a['canonical_url']]:
            key = normalize_url(url)
            if key:
                aliases[key].add(a['article_id'])
    ambiguous_aliases = set().union(*(ids for ids in aliases.values() if len(ids) > 1)) if aliases else set()
    dataset = []
    for pair in pairs:
        a = by_id[pair['article_id']]
        group = dataset_group(pair)
        label, label_status = label_for(pair, config['citation_threshold'])
        index = corpus_index.get(a['article_id'])
        similarity = None
        if a['article_id'] in vectors:
            import numpy as np
            similarity = float(np.clip(np.dot(vectors[a['article_id']], query_vectors[pair['query_text']]), -1, 1))
        reasons = []
        if not a['article_eligible']:
            reasons.append('article_not_eligible')
        if label is None:
            reasons.append(label_status)
        if a['credibility_level'] is None or a['credibility_status'] != 'verified':
            reasons.append('credibility_needs_verification')
        if similarity is None:
            reasons.append('semantic_not_computed')
        if index is not None and not reference:
            reasons.append('bm25_reference_empty')
        alias_review = a['article_id'] in ambiguous_aliases
        if alias_review:
            reasons.append('url_alias_needs_review')
        dataset.append({
            **pair, **{k: v for k, v in a.items() if k != 'text'},
            'dataset_group': group, 'dataset_protocol': DATASET_PROTOCOL,
            'citation_label': label, 'label_status': label_status,
            'citation_threshold': config['citation_threshold'],
            'bm25': bm25[pair['query_text']][index] if index is not None else None,
            'bm25_corpus_sha256': corpus_hash, 'bm25_corpus_scope': 'eligible_google_top10_articles',
            'semantic_cosine': similarity,
            'semantic_status': semantic_status if similarity is not None else 'not_computed',
            'embedding_n_chunks': semantic_metadata.get(a['article_id'], {}).get('n_chunks'),
            'url_alias_needs_review': alias_review, 'ready_for_analysis': not reasons,
            'ready_for_model': not reasons and group == 'google_top10',
            'not_ready_reason': '|'.join(reasons + (['supplement_not_primary'] if group == 'gemini_only' else [])),
            'feature_version': config['feature_version'],
        })
    write_csv(output / 'articles.csv', articles, list(articles[0]))
    fields = list(dict.fromkeys(key for row in dataset for key in row))
    model_fields = ['source_batch', 'pair_id', 'query_id', 'article_id', 'domain', 'citation_label'] + MODEL_FEATURE_FIELDS + EXTRA_FEATURES
    primary, supplement, ready = export_datasets(output, dataset, fields, model_fields)
    write_json(output / 'feature_columns.json', {
        'model_features': MODEL_FEATURE_FIELDS + EXTRA_FEATURES,
        'dataset_protocol': DATASET_PROTOCOL, 'training_scope': 'google_top10',
        'primary_dataset': 'dataset.csv', 'supplementary_dataset': 'dataset_gemini_only.csv',
        'target': 'citation_label', 'identifiers_not_features': model_fields[:5],
        'excluded_from_features': ['candidate_origin', 'in_google_top10', 'in_gemini_citations',
                                   'n_cited', 'n_valid', 'citation_proportion', 'google_positions',
                                   'crawl_status', 'extraction_method', 'credibility_status',
                                   'dataset_group', 'dataset_protocol', 'ready_for_analysis'],
    })
    summary = {
        'created_at': now(), 'config': config, 'attempted_urls': len(articles),
        'article_eligible': len(corpus), 'pairs': len(dataset), 'model_ready_pairs': len(ready),
        'dataset_protocol': DATASET_PROTOCOL,
        'primary_pairs': len(primary), 'supplementary_pairs': len(supplement),
        'primary_unique_urls': len({p['article_id'] for p in primary}),
        'supplementary_unique_urls': len({p['article_id'] for p in supplement}),
        'supplementary_ready_for_analysis': sum(p['ready_for_analysis'] for p in supplement),
        'primary_labels': dict(Counter(str(p['citation_label']) for p in primary)),
        'supplementary_labels': dict(Counter(str(p['citation_label']) for p in supplement)),
        'crawl_status': dict(Counter(a['crawl_status'] for a in articles)),
        'article_review_status': dict(Counter(a['article_review_status'] for a in articles)),
        'label_status': dict(Counter(p['label_status'] for p in dataset)),
        'labels': dict(Counter(str(p['citation_label']) for p in dataset)),
        'bm25_corpus_sha256': corpus_hash, 'bm25_corpus_articles': len(reference),
        'bm25_corpus_scope': 'eligible_google_top10_articles',
        'note': 'dataset.csv/model_ready.csv hanya Google Top-10; dataset_gemini_only.csv tambahan; dataset_union.csv arsip audit. BM25 memakai korpus artikel eligible Google Top-10. Contoh teknis, belum sampel representatif.',
    }
    write_json(output / 'summary.json', summary)
    print(json.dumps({k: v for k, v in summary.items() if k != 'config'}, ensure_ascii=False, indent=2))
    print('Dataset:', output / 'dataset.csv')
    return dataset


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs/article_features.json')
    parser.add_argument('--with-embeddings', action='store_true', help='Embedding lokal; unduh model sekali bila belum tersedia.')
    parser.add_argument('--reextract', action='store_true', default=True, help='Ekstrak ulang HTML lokal (default); tanpa scraping ulang.')
    args = parser.parse_args()
    build(read_json(args.config), with_embeddings=args.with_embeddings, reextract=args.reextract)


if __name__ == '__main__':
    main()
