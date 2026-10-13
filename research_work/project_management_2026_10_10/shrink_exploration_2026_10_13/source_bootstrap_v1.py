"""Snapshot public supplier terms and inspect its documented download catalog."""
from pathlib import Path
import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.request import Request, urlopen

PRIVATE = Path(__file__).resolve().parents[3] / 'data/shrink-cdd-20261013-v1'
PAGES = {
    'terms': 'https://www.cryptodatadownload.com/terms-of-use/',
    'about': 'https://www.cryptodatadownload.com/about/',
    'bitstamp_catalog': 'https://www.cryptodatadownload.com/data/bitstamp/',
}

def main():
    PRIVATE.mkdir(parents=True, exist_ok=True)
    evidence = {}
    for name, url in PAGES.items():
        with urlopen(Request(url, headers={'User-Agent': 'DeReFusion-local-research/1.0'}), timeout=45) as response:
            content = response.read()
            final_url, status = response.url, response.status
        html = content.decode('utf-8', errors='replace')
        path = PRIVATE / (name + '.html')
        if path.exists():
            raise RuntimeError('Refusing to overwrite a supplier snapshot')
        path.write_bytes(content)
        evidence[name] = {'requested_url': url, 'final_url': final_url,
                         'status': status, 'path': str(path),
                         'sha256': hashlib.sha256(content).hexdigest(),
                         'captured_at_utc': datetime.now(timezone.utc).isoformat()}
        if name == 'bitstamp_catalog':
            print('catalog scripts:', re.findall(r'<script[^>]+src=[\"\x27]([^\"\x27]+)', html))
            for line in html.splitlines():
                if any(t in line.lower() for t in ['csv', 'ajax', 'metadata', 'fetch(', 'endpoint']):
                    print(line.strip()[:700])
    (PRIVATE / 'SUPPLIER_SNAPSHOTS.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    print(json.dumps({'supplier_snapshots': evidence}, indent=2))

if __name__ == '__main__':
    main()
