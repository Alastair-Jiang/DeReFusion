"""Collect repository path metadata, not dataset or experiment payload values.

Full path inventory remains local under research_work/project_management_2026_10_10.
This is an inventory utility, not a training launcher or authorization enforcer.
"""
import collections
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT_ROOT = ROOT / 'research_work/project_management_2026_10_10'


def git(*args):
    p = subprocess.run(['git', '-c', 'core.longpaths=true', *args], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return p.stdout, p.stderr.decode('utf-8', errors='replace')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    start = dt.datetime.now(dt.timezone.utc)
    out = OUT_ROOT / start.strftime('%Y%m%dT%H%M%S%fZ')
    out.mkdir(parents=True, exist_ok=False)
    tracked, tw = git('ls-files', '-z')
    untracked, uw = git('ls-files', '--others', '--exclude-standard', '-z')
    ignored, iw = git('ls-files', '--others', '--ignored', '--exclude-standard', '-z')
    sets = {k: set(v.decode('utf-8').split('\0')) - {''} for k, v in
            [('tracked', tracked), ('untracked', untracked), ('ignored', ignored)]}
    head = git('rev-parse', 'HEAD')[0].decode().strip()
    branch = git('branch', '--show-current')[0].decode().strip()
    status = git('status', '--porcelain=v1', '-z')[0]
    (out / 'git_status_before.nul').write_bytes(status)
    (out / 'worktrees.txt').write_bytes(git('worktree', 'list', '--porcelain')[0])
    counts = collections.Counter()
    groups = collections.defaultdict(collections.Counter)
    exts = collections.defaultdict(collections.Counter)
    errors, links, seen, attempt_dirs = [], [], set(), set()
    # Extended-length prefix keeps the Windows metadata walk independent of MAX_PATH.
    scan_root = '\\\\?\\' + str(ROOT) if os.name == 'nt' else str(ROOT)
    def onerror(e):
        errors.append({'path': str(e.filename), 'error': str(e)})
    with (out / 'paths.jsonl').open('w', encoding='utf-8', newline='\n') as sink:
        for current, dirs, files in os.walk(scan_root, followlinks=False, onerror=onerror):
            rel_dir = os.path.relpath(current, scan_root).replace('\\', '/')
            kept = []
            for name in dirs:
                rel = name if rel_dir == '.' else rel_dir + '/' + name
                p = Path(current) / name
                if name == '.git' or rel == 'research_work/project_management_2026_10_10':
                    continue
                if p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()):
                    links.append(rel)
                else:
                    kept.append(name)
            dirs[:] = kept
            if '__attempt-' in rel_dir or '/attempts/' in rel_dir:
                attempt_dirs.add(rel_dir)
            for name in files:
                rel = name if rel_dir == '.' else rel_dir + '/' + name
                if rel == '.git':
                    continue
                p = Path(current) / name
                try:
                    if p.is_symlink():
                        links.append(rel)
                        continue
                    st = p.stat()
                except OSError as e:
                    onerror(e)
                    continue
                seen.add(rel)
                state = next((k for k, v in sets.items() if rel in v), 'unclassified')
                group = rel.split('/')[0] if '/' in rel else '[root]'
                ext = Path(name).suffix.lower() or '[none]'
                counts[state] += 1
                groups[group][state] += 1
                groups[group]['bytes'] += st.st_size
                exts[state][ext] += 1
                sink.write(json.dumps({'path': rel, 'git_state': state, 'bytes': st.st_size,
                                       'mtime_ns': st.st_mtime_ns}, ensure_ascii=False) + '\n')
    pin_paths = [
        'docs/EXPERIMENTAL_DOCTRINE.md', 'docs/PHASE1_PREREGISTRATION.md',
        'docs/PHASE1_EXECUTION_DECISION_V1.2.json',
        'docs/DRF_PROJECT_CONTROL_INDEX_V1_2026-10-08.md',
        'docs/PROJECT_EXPERIMENT_DATA_INVENTORY_AND_GAPS_V1_2026-10-10.md',
        'docs/DATASET_RIGHTS_REVIEW_V1_2026-10-10.md',
        'docs/DATASET_RIGHTS_REVIEW_LEDGER_V1_2026-10-10.csv',
        'reproduction/results/dataset_registry.csv',
        'reports/README.md', 'reports/phase1/phase1-experiment-data-and-progress-20260930.md',
        'reports/phase1/phase1-next-steps-gate-20260930.md',
        'dataset/README.md', 'data/raw/yahoo/DOWNLOAD_LINKS.md',
    ]
    lead = 'research_work/forward_increment/lead_design_2026_10_07/'
    pin_paths += [lead + p for p in ['R1_APPROVED_DESIGN_V1.json',
        'DELEGATED_LEAD_APPROVAL_R1_V1.md', 'project_synthesis_v1/R1_EXECUTION_GATE_DECISION_V1.md',
        'project_synthesis_v1/PROJECT_ASSESSMENT_AND_ROADMAP.md',
        'project_synthesis_v1/EVIDENCE_INDEX.json', 'project_synthesis_v1/DELIVERABLE_HASHES.json']]
    pin_paths += [f'reproduction/results/phase1/{name}.manifest.csv' for name in
                  ['A_calibration', 'B_screen', 'C_confirmation', 'D_temporal_robustness']]
    pins = {p: {'sha256': digest(ROOT / p), 'bytes': (ROOT / p).stat().st_size,
                'tracked': p in sets['tracked']} for p in pin_paths if (ROOT / p).is_file()}
    missing_pins = [p for p in pin_paths if not (ROOT / p).is_file()]
    # Receipt metadata only: never open prediction/target arrays or weights.
    receipt_rows, receipt_errors = [], []
    fields = ['protocol_version', 'logical_run_id', 'attempt_id', 'attempt', 'asset',
              'model', 'horizon', 'seed', 'status', 'git_commit', 'dataset_sha256',
              'created_at_utc', 'scientific_use', 'supersedes_attempt', 'batch_id',
              'execution_track', 'execution_device', 'authorization_commit',
              'environment_fingerprint_sha256', 'split_manifest_id', 'prediction_keys_sha256']
    for rel in sorted(seen):
        if not rel.startswith('reproduction/results/phase1/'):
            continue
        if not (Path(rel).name.startswith('receipt') and rel.endswith('.json')):
            continue
        try:
            raw = (ROOT / rel).read_bytes()
            data = json.loads(raw.decode('utf-8-sig'))
            if not isinstance(data, dict):
                raise ValueError('receipt root is not an object')
            row = {k: data.get(k) for k in fields}
            row.update(path=rel, receipt_sha256=hashlib.sha256(raw).hexdigest(),
                       evidence_level='parsed_metadata_only_not_reaudited',
                       absent_inline_fields=[k for k in fields if data.get(k) is None],
                       archived_filename=Path(rel).name != 'receipt.json',
                       environment_present=bool(data.get('environment') or data.get('environment_fingerprint_sha256')),
                       config_fingerprint_present=bool(data.get('config_fingerprint')))
            receipt_rows.append(row)
        except (OSError, ValueError, UnicodeError) as e:
            receipt_errors.append({'path': rel, 'error': type(e).__name__})
    with (out / 'receipt_metadata.jsonl').open('w', encoding='utf-8') as sink:
        for row in receipt_rows:
            sink.write(json.dumps(row, ensure_ascii=False) + '\n')
    def tree_candidates(ref):
        raw, _ = git('ls-tree', '-r', '-l', '-z', ref)
        found = []
        for item in raw.decode('utf-8').split('\0'):
            if not item:
                continue
            metadata, path = item.split('\t', 1)
            mode, kind, oid, size = metadata.split()
            if path.startswith('dataset/') or Path(path).suffix.lower() in {
                    '.npy', '.npz', '.pth', '.pt', '.ckpt', '.bin', '.pkl', '.pickle'}:
                found.append({'path': path, 'blob_oid': oid, 'git_blob_bytes': int(size),
                              'classification': 'path_or_extension_candidate_not_content_audit'})
        return found
    exposures = {ref: tree_candidates(ref) for ref in ['HEAD', 'origin/main']}
    (out / 'tracked_payload_candidates.json').write_text(
        json.dumps(exposures, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    final_head = git('rev-parse', 'HEAD')[0].decode().strip()
    summary = {'schema_version': 1, 'started_at_utc': start.isoformat(),
        'finished_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        'repository': str(ROOT), 'branch': branch, 'head': head,
        'head_unchanged': head == final_head,
        'scan_exclusions': ['.git directories and root .git file',
                            'symlinks/junctions (listed separately)',
                            'research_work/project_management_2026_10_10 (output)',
                            'other checkouts and external/cloud storage'],
        'payload_values_read': False, 'counts': dict(counts),
        'git_enumerated_counts': {k: len(v) for k, v in sets.items()},
        'tracked_paths_not_seen': sorted(sets['tracked'] - seen),
        'groups': {k: dict(v) for k, v in sorted(groups.items())},
        'extensions': {k: dict(sorted(v.items())) for k, v in exts.items()},
        'walk_errors': errors, 'skipped_links': links,
        'git_warnings': [w for w in [tw, uw, iw] if w],
        'attempt_named_directory_candidates': len(attempt_dirs),
        'attempt_count_caveat': 'Path heuristic includes synthetic, duplicate and child folders; not a run count.',
        'collector_sha256': digest(Path(__file__)),
        'receipt_metadata': {'parsed': len(receipt_rows), 'errors': receipt_errors,
            'archived_filenames': sum(r['archived_filename'] for r in receipt_rows),
            'status_statements': dict(collections.Counter(str(r['status']) for r in receipt_rows)),
            'distinct_receipt_sha256': len({r['receipt_sha256'] for r in receipt_rows}),
            'absent_inline_field_counts': dict(collections.Counter(k for r in receipt_rows for k in r['absent_inline_fields'])),
            'missing_environment': sum(not r['environment_present'] for r in receipt_rows),
            'missing_config_fingerprint': sum(not r['config_fingerprint_present'] for r in receipt_rows),
            'index_sha256': digest(out / 'receipt_metadata.jsonl'),
            'interpretation': 'Records and status statements, not completed/eligible/independently audited runs. Absent inline fields may be optional or in linked manifests; do not call them missing evidence before joining. Authorization commit is not necessarily run code commit.'},
        'tracked_payload_candidates': {ref: {'count': len(rows),
            'extensions': dict(collections.Counter(Path(r['path']).suffix.lower() for r in rows)),
            'git_blob_bytes': sum(r['git_blob_bytes'] for r in rows)} for ref, rows in exposures.items()},
        'tracked_payload_candidate_index_sha256': digest(out / 'tracked_payload_candidates.json'),
        'input_pins': pins, 'missing_pin_paths': missing_pins,
        'local_path_manifest_sha256': digest(out / 'paths.jsonl')}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'output': str(out), 'counts': dict(counts), 'walk_errors': len(errors),
                      'git_warnings': len(summary['git_warnings']), 'head_unchanged': head == final_head}, ensure_ascii=False))


if __name__ == '__main__':
    main()
