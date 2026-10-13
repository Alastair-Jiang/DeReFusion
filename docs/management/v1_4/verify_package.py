"""Read-only verification of this management package; never launches experiments."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess

PACKAGE = Path(__file__).resolve().parent
ROOT = PACKAGE.parents[2]


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    errors = []

    def check(ok, message):
        if not ok:
            errors.append(message)

    manifest = read(PACKAGE / 'hashes.json')
    files = {p.name for p in PACKAGE.iterdir() if p.is_file() and p.name != 'hashes.json'}
    check(files == set(manifest['files']), 'Package file set changed')
    for name, expected in manifest['files'].items():
        p = PACKAGE / name
        check(p.is_file() and digest(p) == expected, 'Package drift: ' + name)
    baseline = read(PACKAGE / 'baseline.json')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    ancestry = subprocess.run(['git', 'merge-base', '--is-ancestor', baseline['head'], head],
                             cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    baseline_is_ancestor = ancestry.returncode == 0
    check(baseline_is_ancestor, 'Baseline HEAD is not an ancestor; rebaseline before relying on current-state claims')
    artifact_index = read(PACKAGE / 'receipt_environment_artifact_index.json')
    check(artifact_index.get('head') == baseline['head'], 'Artifact index HEAD differs from baseline')
    check(all(artifact.get('content_hash_checked') is False
              for record in artifact_index.get('records', [])
              for artifact in record.get('declared_artifacts', [])),
          'Artifact index contains a content-hash verification claim')
    check(bool(artifact_index.get('records')), 'Artifact index has no receipt records')
    review = baseline.get('dsh_review_v1_1', {})
    review_report = ROOT / review.get('report_path', '')
    check(review_report.is_file() and digest(review_report) == review.get('report_sha256'),
          'DSH v1.1 review report missing or hash mismatch')
    pins = baseline['input_pins']
    for name, info in pins.items():
        p = ROOT / name
        check(p.is_file() and digest(p) == info['sha256'], 'Input drift: ' + name)
    for info in baseline['rechecked_evidence'] + baseline['rechecked_model_sources']:
        p = ROOT / info['path']
        check(p.is_file() and digest(p) == info['expected'], 'Evidence drift: ' + info['path'])
    for name, expected in baseline['preexisting_tracked_modifications'].items():
        check(digest(ROOT / name) == expected, 'Preexisting modification changed: ' + name)
    with (PACKAGE / 'datasets.csv').open(encoding='utf-8', newline='') as f:
        datasets = list(csv.DictReader(f))
    check(len(datasets) == 61 and len({r['file'] for r in datasets}) == 61, 'Dataset cardinality')
    check(all(not r['current_raw_sha256'] for r in datasets), 'Unexpected raw-data validation claim')
    gaps = read(PACKAGE / 'gaps.json')['gaps']
    ids = {g['id'] for g in gaps}
    check(len(ids) == len(gaps), 'Duplicate gap ID')
    check(all(set(g['dependencies']) <= ids for g in gaps), 'Unknown gap dependency')
    release = read(PACKAGE / 'r1_release_candidate.json')
    check(release['state'] == 'DRAFT_BLOCKED' and release['execution_permitted'] is False,
          'This package must not masquerade as a run release')
    check(release['issued_at'] is None and release['issued_by'] is None, 'Unexpected release issuer')
    design = read(ROOT / release['protocol_path'])
    check(digest(ROOT / release['protocol_path']) == release['protocol_sha256'], 'Design drift')
    for key in ('protocol_id', 'assets', 'resource_limits', 'planned_workload'):
        check(release[key] == design[key], 'Design mismatch: ' + key)
    check(not read(PACKAGE / 'authorization.json')['real_run_release_issued'], 'False release claim')
    result = {'passed': not errors, 'errors': errors, 'package_files': len(files),
              'input_pins': len(pins), 'evidence_entries': len(baseline['rechecked_evidence']),
              'model_pins': len(baseline['rechecked_model_sources']), 'datasets': len(datasets),
              'gaps': len(gaps), 'head': head, 'baseline_head': baseline['head'],
              'baseline_head_is_ancestor': baseline_is_ancestor, 'payload_values_read': False,
              'independent_review': False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not errors else 1)


if __name__ == '__main__':
    main()
