"""Conservative publisher date parsing; never infer dates from crawl time/URL."""
import re
from datetime import datetime, timezone

from dateutil.parser import isoparse, parse

MONTHS = {
    'januari': 'January', 'februari': 'February', 'maret': 'March',
    'april': 'April', 'mei': 'May', 'juni': 'June', 'juli': 'July',
    'agustus': 'August', 'agu': 'Aug', 'agt': 'Aug', 'september': 'September',
    'oktober': 'October', 'okt': 'Oct', 'november': 'November',
    'desember': 'December', 'des': 'Dec',
}
MONTH_PATTERN = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'


def parse_publication_date(value):
    """Only full ISO dates or explicit day + named month + year are accepted.

    Numeric day/month dates remain ambiguous. Missing timezone uses UTC, with
    that assumption separately recorded. Missing day/year is never filled in.
    """
    text = re.sub(r'\s+', ' ', str(value or '')).strip()
    if not text:
        return None
    # Some publisher ISO timestamps use dots in the clock component.
    text = re.sub(r'(T\d{2})\.(\d{2})\.(\d{2})', r'\1:\2:\3', text)
    try:
        if re.match(r'^(?:\d{4}-\d{2}-\d{2}|\d{8})(?:$|[Tt ])', text):
            return isoparse(text)
        for local, english in MONTHS.items():
            text = re.sub(r'\b' + local + r'\b', english, text, flags=re.I)
        text = re.sub(r'^(?:dipublikasikan|diterbitkan|published)(?:\s+(?:pada|on))?\s*:?\s*', '', text, flags=re.I)
        text = re.sub(r'^(?:senin|selasa|rabu|kamis|jumat|jum\x27at|sabtu|minggu),?\s+', '', text, flags=re.I)
        # Fullmatch prevents using copyright/related dates inside arbitrary text.
        date = rf'(?:\d{{1,2}}\s+{MONTH_PATTERN}\s+\d{{4}}|{MONTH_PATTERN}\s+\d{{1,2}},?\s+\d{{4}})'
        clock = r'(?:\s*(?:,|\||-)?\s*(?:pukul\s+)?\d{1,2}[:.]\d{2}(?::\d{2})?(?:\s*(?:AM|PM))?(?:\s*(?:WIB|WITA|WIT|UTC|GMT|[+-]\d{2}:?\d{2}))?)?'
        if not re.fullmatch(date + clock, text, re.I):
            return None
        text = re.sub(r'\b(\d{1,2})\.(\d{2})\b', r'\1:\2', text)
        text = re.sub(r'\s+[|,-]\s+|\bpukul\s+', ' ', text, flags=re.I)
        return parse(text, fuzzy=False, default=datetime(2000, 1, 1),
                     tzinfos={'WIB': 7 * 3600, 'WITA': 8 * 3600, 'WIT': 9 * 3600})
    except (ValueError, TypeError, OverflowError):
        return None


def publication_details(value, retrieved_at):
    published = parse_publication_date(value)
    result = {'published_at_normalized': '', 'publication_age_days': None,
              'publication_age_status': 'missing_publication_date' if not value else 'unparseable_publication_date',
              'publication_timezone_assumed': False}
    if published is None:
        return result
    result['publication_timezone_assumed'] = published.tzinfo is None
    published = published.replace(tzinfo=published.tzinfo or timezone.utc)
    result['published_at_normalized'] = published.isoformat()
    try:
        retrieved = isoparse(retrieved_at)
        retrieved = retrieved.replace(tzinfo=retrieved.tzinfo or timezone.utc)
    except (ValueError, TypeError, OverflowError):
        result['publication_age_status'] = 'invalid_retrieval_date'
        return result
    age = (retrieved - published).total_seconds() / 86400
    result['publication_age_status'] = 'future_publication_date' if age < 0 else 'available'
    if age >= 0:
        result['publication_age_days'] = round(age, 3)
    return result
