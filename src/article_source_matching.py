"""Evidence-based URL identity and relabeling from saved Gemini trials only."""
import hashlib
import json
from collections import defaultdict

from collect_paa import read_json
from collect_main_dataset import normalize_url, trial_info
from pilot_gemini_grounding import destination_url

VERSION = 'saved_trials_redirect_content_v1'


class ArticleIdentities:
    """Require fetched redirects or identical content plus a shared canonical."""
    def __init__(self, articles):
        self.parent, self.evidence = {}, []
        self.articles = {a['article_id']: a for a in articles}
        candidates = defaultdict(set)
        signatures = {}
        for a in articles:
            aid = a['article_id']
            for url in (a['article_url'], a.get('final_url'), a.get('canonical_url')):
                key = normalize_url(url)
                if key:
                    candidates[key].add(aid)
            if a['crawl_status'] == 'success':
                self.join(a['article_url'], a['final_url'], 'observed_scrape_redirect')
            text = ' '.join((a.get('text') or '').split())
            title = ' '.join((a.get('title') or '').split())
            if a['crawl_status'] == 'success' and len(text.split()) >= 100 and title:
                signatures[aid] = hashlib.sha256((title + '\n' + text).encode()).hexdigest()
        # Canonical tags alone can point to homepages or translated/different pages.
        for url, ids in candidates.items():
            if len(ids) < 2:
                continue
            by_content = defaultdict(list)
            for aid in sorted(ids):
                if aid in signatures:
                    by_content[signatures[aid]].append(aid)
            for signature, matching in by_content.items():
                if len(matching) < 2:
                    continue
                # Do not use a canonical URL that is shared by differing content.
                if set(matching) != ids:
                    continue
                for aid in matching:
                    self.join(self.articles[aid]['article_url'], url,
                              'same_canonical_and_identical_title_text', signature)
        self.unresolved = set()
        for ids in candidates.values():
            if len(ids) > 1 and len({self.identity(self.articles[i]['article_url']) for i in ids}) > 1:
                self.unresolved.update(ids)

    def identity(self, url):
        key = normalize_url(url)
        if not key:
            return ''
        self.parent.setdefault(key, key)
        if self.parent[key] != key:
            self.parent[key] = self.identity(self.parent[key])
        return self.parent[key]

    def join(self, left, right, reason, signature=''):
        a, b = self.identity(left), self.identity(right)
        if not a or not b or a == b:
            return
        self.parent[max(a, b)] = min(a, b)
        self.evidence.append({'left_url': left, 'right_url': right,
                              'basis': reason, 'content_sha256': signature})


def reconcile_pairs(pairs, articles, root, recovery_cache):
    """Return derived labels + duplicate markers; never edit manifests or raw trials."""
    identities = ArticleIdentities(articles)
    by_id = {a['article_id']: a for a in articles}
    cache = read_json(recovery_cache) if recovery_cache.exists() else {}
    query_context = {}
    audit = {'version': VERSION, 'url_evidence': identities.evidence, 'raw_record_sha256': {},
             'recovered_url_count': sum(bool(destination_url(v)) for v in cache.values()),
             'recovery_cache_sha256': (hashlib.sha256(recovery_cache.read_bytes()).hexdigest()
                                       if recovery_cache.exists() else ''),
             'used_recovery_evidence': {}}

    def known(url, resolutions):
        saved = destination_url(resolutions.get(url, {}))
        if saved:
            return saved
        recovered = destination_url(cache.get(url, {}))
        if recovered:
            audit['used_recovery_evidence'][url] = cache[url]
        return recovered

    for pair in pairs:
        key = (pair['source_batch'], pair['query_id'])
        if key in query_context:
            continue
        path = root / 'data/raw/main' / key[0] / 'queries' / (key[1] + '.json')
        if not path.exists():
            query_context[key] = None
            continue
        record = read_json(path)
        audit['raw_record_sha256'][str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
        trials = []
        for trial in record.get('trials', []):
            valid, _, _, web, cited = trial_info(trial)
            if not valid:
                continue
            urls, unknown = set(), False
            for index in cited:
                source = known(web[index]['uri'], trial.get('url_resolutions', {}))
                if source:
                    urls.add(identities.identity(source))
                else:
                    unknown = True
            trials.append((urls, unknown))
        google_resolutions = record.get('google', {}).get('url_resolutions', {})
        # Manifest article URLs are already normalized destinations. Their raw
        # Google link can differ (tracking parameters, translation, redirects).
        google_destinations = {identities.identity(known(url, google_resolutions))
                               for url in google_resolutions}
        google_destinations.discard('')
        query_context[key] = (trials, google_resolutions, google_destinations)

    result = []
    for old in pairs:
        pair = dict(old)
        a = by_id[pair['article_id']]
        identity = identities.identity(a['article_url'])
        pair.update(article_identity_url=identity, matching_version=VERSION,
                    url_alias_needs_review=pair['article_id'] in identities.unresolved,
                    matching_applied=False, duplicate_pair_of='')
        context = query_context[(pair['source_batch'], pair['query_id'])]
        if context is not None:
            trials, google_resolutions, google_destinations = context
            if len(trials) != int(pair['n_valid']) or len(trials) < 2:
                raise ValueError('Raw trials berbeda dari manifest; jangan melabeli snapshot yang berubah.')
            target = known(pair['article_url'], google_resolutions)
            destination_known = bool(target or identity in google_destinations or
                                     a['crawl_status'] == 'success' or
                                     pair.get('in_google_top10') == 'False')
            targets = {identity}
            if target:
                targets.add(identities.identity(target))
            n_cited = sum(bool(targets & urls) for urls, _ in trials)
            n_unknown = sum(not bool(targets & urls) and (unknown or not destination_known)
                            for urls, unknown in trials)
            for name in ('n_cited', 'n_unknown_matches', 'citation_proportion', 'citation_lower',
                         'citation_upper', 'candidate_origin', 'in_gemini_citations',
                         'citation_label', 'label_status'):
                pair['original_' + name] = pair.get(name, '')
            lower, upper = n_cited / len(trials), (n_cited + n_unknown) / len(trials)
            pair.update(n_cited=str(n_cited), n_unknown_matches=str(n_unknown),
                        citation_lower=str(lower), citation_upper=str(upper),
                        citation_proportion=str(lower) if not n_unknown else '',
                        in_gemini_citations=str(n_cited > 0), matching_applied=True)
            if pair['in_google_top10'] == 'True':
                pair['candidate_origin'] = 'google_and_gemini' if n_cited else 'google_only'
            elif not n_cited:
                raise ValueError('Sitasi sumber tambahan hilang saat pencocokan ulang; periksa bukti.')
        result.append(pair)

    # Retain duplicate rows for audit, but only one representative can enter a model.
    groups = defaultdict(list)
    for pair in result:
        groups[(pair['source_batch'], pair['query_id'], pair['article_identity_url'])].append(pair)
    for group in groups.values():
        if len(group) < 2:
            continue
        first = min(group, key=lambda p: (p['in_google_top10'] != 'True',
                    not by_id[p['article_id']]['article_eligible'], p['pair_id']))
        for pair in group:
            if pair is not first:
                pair['duplicate_pair_of'] = first['pair_id']
    audit['confirmed_duplicate_pairs'] = sum(bool(p['duplicate_pair_of']) for p in result)
    audit['unresolved_alias_articles'] = len(identities.unresolved)
    return result, audit
