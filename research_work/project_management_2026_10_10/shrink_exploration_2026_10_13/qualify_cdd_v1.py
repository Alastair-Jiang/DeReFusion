"""Bounded acquisition/QA under the CDD local-research qualification release."""
from pathlib import Path
from datetime import datetime, timezone, date, timedelta
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import csv
import hashlib
import io
import json
import math
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIVATE = ROOT / 'data/shrink-cdd-20261013-v1'
RELEASE = HERE / 'CDD_LOCAL_RESEARCH_QUALIFICATION_RELEASE_V1.json'
SYMBOLS = {'BTCUSD': 'BTC/USD', 'ETHUSD': 'ETH/USD'}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def fetch(url, limit=2097152):
    if urlparse(url).hostname not in {'api.cryptodatadownload.com', 'www.cryptodatadownload.com'}:
        raise ValueError('Unapproved supplier host')
    with urlopen(Request(url, headers={'User-Agent': 'DeReFusion-local-research/1.0'}), timeout=45) as r:
        if urlparse(r.url).hostname not in {'api.cryptodatadownload.com', 'www.cryptodatadownload.com'}:
            raise ValueError('Unapproved redirect')
        body = r.read(limit + 1)
        if len(body) > limit:
            raise ValueError('Download byte limit exceeded')
        return body, {'url': url, 'final_url': r.url, 'http_status': r.status,
                      'fetched_at_utc': datetime.now(timezone.utc).isoformat(),
                      'sha256': digest(body), 'bytes': len(body)}

def main():
    release = json.loads(RELEASE.read_text(encoding='utf-8'))
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    if head != release['head'] or release['decision'] != 'APPROVED_FOR_BOUNDED_LOCAL_NONCOMMERCIAL_RESEARCH_QUALIFICATION':
        raise ValueError('Release identity mismatch')
    for name in ['terms', 'about', 'catalog']:
        fn = 'bitstamp_catalog' if name == 'catalog' else name
        expected = release['basis'][name + '_html_sha256']
        if digest((PRIVATE / (fn + '.html')).read_bytes()) != expected:
            raise ValueError('Supplier snapshot hash drift')
    output = HERE / 'CDD_QUALIFICATION_RESULTS_V1.json'
    if output.exists():
        raise ValueError('Refusing to overwrite a completed QA record')
    record = {'release_id': release['release_id'], 'release_sha256': digest(RELEASE.read_bytes()),
              'script_sha256': digest(Path(__file__).read_bytes()), 'head': head,
              'tracked_diff_sha256': digest(subprocess.check_output(['git', 'diff', '--binary'], cwd=ROOT)),
              'started_at_utc': datetime.now(timezone.utc).isoformat(),
              'assets': {}, 'scope': 'Local non-commercial QA only; no training/scoring; old Yahoo files untouched'}
    catalog_body, catalog_meta = fetch(release['catalog_url'])
    (PRIVATE / 'catalog.json').write_bytes(catalog_body)
    record['catalog'] = catalog_meta
    rows = json.loads(catalog_body)['data']
    for asset, symbol in SYMBOLS.items():
        row = [r for r in rows if r['symbol'] == symbol and r['timeframe'] == 'day']
        if len(row) != 1:
            raise ValueError('Missing or ambiguous daily catalog row: ' + asset)
        raw_path = PRIVATE / (asset + '.raw.csv')
        if raw_path.exists():
            raise ValueError('Raw input already exists; no overwrite/retry')
        body, meta = fetch(row[0]['file'])
        raw_path.write_bytes(body)
        lines = body.decode('utf-8-sig').splitlines()
        if lines[0].startswith('http'):
            lines = lines[1:]
        reader = csv.DictReader(lines)
        cols = {k.lower(): k for k in reader.fieldnames}
        if not all(c in cols for c in ['unix', 'date', 'symbol', 'open', 'high', 'low', 'close']):
            raise ValueError('Unexpected schema: ' + asset)
        dates = []
        timestamp_units = set()
        mismatch = 0
        for r in reader:
            ts = float(r[cols['unix']])
            unit = 'milliseconds' if ts >= 1e12 else 'seconds'
            timestamp_units.add(unit)
            if unit == 'milliseconds':
                ts /= 1000
            dt = datetime.fromtimestamp(ts, timezone.utc)
            if dt.hour or dt.minute or dt.second or dt.microsecond:
                raise ValueError('Daily timestamp not UTC midnight: ' + asset)
            if dt.date() >= date(2026, 1, 1):
                continue  # Do not parse OHLC values outside the exploratory interval.
            if r[cols['symbol']].replace('/', '') != asset:
                raise ValueError('Unexpected symbol: ' + asset)
            values = [float(r[cols[c]]) for c in ['open', 'high', 'low', 'close']]
            o, h, l, c = values
            if not all(math.isfinite(v) and v > 0 for v in values) or h < max(o, c, l) or l > min(o, c, h):
                raise ValueError('Invalid OHLC: ' + asset)
            dates.append(dt.date())
            mismatch += r[cols['date']][:10] != dt.date().isoformat()
        if len(set(dates)) != len(dates):
            raise ValueError('Duplicate date: ' + asset)
        wanted = [date(2018, 1, 1) + timedelta(days=i) for i in range((date(2026,1,1)-date(2018,1,1)).days)]
        missing = sorted(set(wanted) - set(dates))
        item = {**meta, 'catalog_entry': row[0], 'local_path': str(raw_path),
                'columns': reader.fieldnames, 'timestamp_units': sorted(timestamp_units),
                'time_grid': 'UTC daily candle starts; 24/7 calendar',
                'source_label_date_mismatches': mismatch,
                'reviewed_price_interval': 'available history before 2026-01-01',
                'planned_interval': '[2018-01-01,2026-01-01)',
                'planned_rows': len(wanted), 'missing_dates': [d.isoformat() for d in missing],
                'observed_min_date': min(dates).isoformat(), 'observed_max_date': max(dates).isoformat(),
                'ohcl_finite_positive_and_range_check': 'PASS',
                'status': 'ELIGIBLE' if not missing and mismatch == 0 else 'REQUIRES_RESOLUTION'}
        record['assets'][asset] = item
        print(json.dumps({'asset': asset, 'status': item['status'], 'rows': len(wanted),
                          'missing_dates': len(missing), 'date_label_mismatches': mismatch,
                          'raw_sha256': meta['sha256']}), flush=True)
    record['result'] = 'PASS' if all(x['status'] == 'ELIGIBLE' for x in record['assets'].values()) else 'REQUIRES_RESOLUTION'
    record['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
    output.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'result': record['result'], 'record': str(output), 'sha256': digest(output.read_bytes())}))

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        failure = HERE / ('CDD_QUALIFICATION_FAILED_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '.json')
        failure.write_text(json.dumps({'result': 'FAILED', 'exception_type': type(e).__name__, 'reason': str(e),
                                       'script_sha256': digest(Path(__file__).read_bytes())}), encoding='utf-8')
        raise
