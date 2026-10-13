"""Export source-only staged bytes and validate without exporting data history."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone
import zipfile

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PRIVATE = ROOT/'data/engineering-cpu-validation-20261013-v1'
EXE = PRIVATE/'.venv/Scripts/python.exe'
DEST = PRIVATE/'staged-source-v1-1'
ZIP = PRIVATE/'STAGED_SOURCE_V1_1.zip'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path, obj):
    assert not path.exists(), 'Preserve existing evidence: '+str(path)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')

assert DEST.resolve().is_relative_to(PRIVATE.resolve()) and not DEST.exists() and not ZIP.exists()
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
assert head == '5a8220ab0fdfb72601671f9fadf7de5e8a3b7554'
tree = subprocess.check_output(['git', 'write-tree'], cwd=ROOT, text=True).strip()
selections = ['.gitattributes', 'models/derefusion/bundle_v3_pin', 'models/derefusion/DeReFusion.py',
              'layers/RevIN.py', 'reproduction/preprocessing',
              'reproduction/analysis/compression_replay.py', 'reproduction/analysis/check_artifact_boundary.py',
              'tests/test_fixed_ohlc_preprocessing.py', 'tests/test_compression_replay.py',
              'requirements/torch-cpu.txt', 'requirements/compression-cpu.txt',
              'requirements/compression-cpu-win311-wheels.txt', 'requirements/torch-cpu-win311-wheel.txt',
              'docs/DRF_ARTIFACT_BOUNDARY_V1_2026-10-13.json',
              'research_work/project_management_2026_10_10/shrink_exploration_2026_10_13',
              'research_work/project_management_2026_10_10/compression_pilot_2026_10_13']
subprocess.run(['git', 'archive', '--format=zip', '--output='+str(ZIP), tree, '--', *selections], cwd=ROOT, check=True)
DEST.mkdir()
with zipfile.ZipFile(ZIP) as z:
    for member in z.infolist():
        assert (DEST/member.filename).resolve().is_relative_to(DEST.resolve()), 'Archive path escape'
    z.extractall(DEST)

# Prove only code/text was exported; no historical datasets/weights included.
exported = [p for p in DEST.rglob('*') if p.is_file()]
assert not [p for p in exported if p.suffix.lower() in {'.npy', '.npz', '.pt', '.pth'}]
for relative, filename in (('shrink_exploration_2026_10_13', 'CDD_DELIVERABLE_HASHES_V1.json'),
                           ('compression_pilot_2026_10_13', 'DELIVERABLE_HASHES_V1.json')):
        manifest = json.loads((DEST/'research_work/project_management_2026_10_10'/relative/filename).read_text(encoding='utf-8'))
        # Reports are not needed for this source-only fixture; validate those
        # present, and require every manifest's code/record member to exist.
        for path, expected in manifest['files'].items():
            assert (DEST/path).is_file(), path
            assert sha(DEST/path) == expected, path

results = []
commands = [['-m', 'pip', 'check'], ['-B', 'research_work/project_management_2026_10_10/compression_pilot_2026_10_13/run_pilot_v1.py', '--help'],
            ['-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_fixed_ohlc_preprocessing.py', '-v'],
            ['-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_compression_replay.py', '-v']]
for args in commands:
    proc = subprocess.run([str(EXE), *args], cwd=DEST, capture_output=True, text=True, timeout=60)
    results.append({'command_args': args, 'returncode': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr})
    assert proc.returncode == 0, proc.stderr

newline_repairs = []
parent = 'research_work/project_management_2026_10_10/shrink_exploration_2026_10_13'
for path in subprocess.check_output(['git', 'ls-files', '--', parent], cwd=ROOT, text=True).splitlines():
    working = (ROOT/path).read_bytes()
    old = subprocess.check_output(['git', 'cat-file', 'blob', 'HEAD:'+path], cwd=ROOT)
    staged = subprocess.check_output(['git', 'cat-file', 'blob', ':'+path], cwd=ROOT)
    assert staged == working, path
    if old != working:
        assert old.replace(b'\r\n', b'\n') == working.replace(b'\r\n', b'\n'), path
        newline_repairs.append({'path': path, 'old_blob_sha256': hashlib.sha256(old).hexdigest(), 'restored_bytes_sha256': sha(ROOT/path)})
assert len(newline_repairs) == 16
env_code = "import importlib.metadata as m,json,sys; print(json.dumps({'python':sys.version,'versions':{n:m.version(n) for n in ['torch','numpy','filelock','typing_extensions','networkx','Jinja2','fsspec','sympy','mpmath','MarkupSafe']}}))"
environment = json.loads(subprocess.check_output([str(EXE), '-B', '-c', env_code], text=True))
assert environment['versions']['torch'] == '2.5.1+cpu' and environment['versions']['numpy'] == '2.1.2'
legacy_untouched = ['docs/DRF_TAKEOVER_STATUS_CORRECTION_V1_2026-10-10.md',
                    'docs/PROJECT_STATUS_AND_EXPERIMENT_CATALOG_V1_2026-10-10.md',
                    'reproduction/analysis/receive_phase1_completed.py',
                    'reproduction/results/phase1/local-5060-manifests/freeze-summary.json',
                    'tests/test_phase1_completed_receiver.py']
staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=ROOT, text=True).splitlines()
assert not set(staged).intersection(legacy_untouched)
receipt = {'status': 'PASS', 'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'repository': str(ROOT),
           'audit_script_sha256': sha(__file__),
           'head_at_validation': head, 'validated_source_stage_tree': tree,
           'source_tree_scope': 'Staged source-only archive, excludes final receipt; not a complete Git checkout or real-data replay',
           'new_real_F_fits': 0, 'new_real_scoring': False, 'test_role_arrays_read': False,
           'fresh_environment': environment, 'targeted_tests': 13, 'source_export_files': len(exported),
           'export_zip_sha256': sha(ZIP), 'source_fixture_path': str(DEST),
           'commands': results, 'newline_only_blob_repairs': newline_repairs,
           'known_existing_user_changes_not_staged': legacy_untouched,
           'K3_independent_engineering_review': 'PENDING', 'full_real_replay_acceptance': 'NOT_RUN',
           'environment_install_route': 'Official CPU wheel; nine exact PyPI wheels resolved and SHA-verified, downloaded with urllib and installed offline after slow pip index/direct network attempts were stopped',
           'engineering_validation_deviations': [{'attempt': 'source export v1', 'reason': 'Helper assumed identical manifest filename for parent and child; corrected to actual CDD_DELIVERABLE_HASHES_V1 vs DELIVERABLE_HASHES_V1', 'preserved_fixture': str(PRIVATE/'staged-source-v1'), 'preserved_zip': str(PRIVATE/'STAGED_SOURCE_V1.zip'), 'impact': 'No frozen code, data or experiment result changed; source verification rerun as v1-1'}],
           'software_download_receipt_sha256': sha(PRIVATE/'LOCAL_WHEEL_DOWNLOAD_RECEIPT.json')}
save(HERE/'VALIDATION_RECEIPT_V1.json', receipt)
files = [ROOT/p for p in staged if (ROOT/p).is_file()]
files.extend(p for p in HERE.iterdir() if p.is_file() and p not in files)
save(HERE/'IMPLEMENTATION_MANIFEST_V1.json', {'head_at_validation': head, 'scope': 'Engineering source and text records; private data/env excluded',
      'self_excluded': True, 'independent_review': 'PENDING', 'files': {p.relative_to(ROOT).as_posix():sha(p) for p in files}})
print(json.dumps({'status': 'PASS', 'fresh_tests': 13, 'newline_repairs': 16, 'source_export_files': len(exported), 'real_fits': 0}))
