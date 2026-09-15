"""Archive public PSE search evidence; a result is not an automatic credibility rank."""
import argparse
from pathlib import Path
import requests
from collect_paa import write_json, digest, now

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = 'https://pse.komdigi.go.id/api/v1/tdpse/tdpse-list'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keywords', nargs='+', required=True)
    args = parser.parse_args()
    for keyword in args.keywords:
        payload = {'keyword': keyword, 'length': 100, 'sort_by': [], 'start': 0}
        record = {'keyword': keyword, 'endpoint': ENDPOINT, 'checked_at': now(), 'request': payload}
        try:
            response = requests.post(ENDPOINT, json=payload, timeout=30)
            record['http_status'] = response.status_code
            response.raise_for_status()
            record['response'] = response.json()
            record['status'] = 'success'
        except (requests.RequestException, ValueError) as exc:
            record['status'] = 'error'
            record['error_type'] = type(exc).__name__
        path = ROOT / 'data/raw/credibility' / (digest(keyword) + '.json')
        if path.exists():
            path = path.with_name(path.stem + '_' + digest(record['checked_at']) + '.json')
        write_json(path, record)
        print(keyword, record['status'], path.relative_to(ROOT), flush=True)


if __name__ == '__main__':
    main()
