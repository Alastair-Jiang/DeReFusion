"""Refresh only report/receipt/manifest hashes after a review-status correction."""
import hashlib, json, pathlib
root = pathlib.Path(__file__).resolve().parents[3]
d = pathlib.Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p, x): p.write_text(json.dumps(x, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
report = root/'docs/DRF_CDD_SHRINK_FIRST_BATCH_RESULTS_2026-10-13.md'
recp = d/'CDD_DSH_REVIEW_DISPOSITION_V1.json'
rec = load(recp)
for k, v in list(rec['verified_artifact_bindings'].items()):
    if k == 'docs/DRF_CDD_SHRINK_FIRST_BATCH_RESULTS_2026-10-13.md':
        rec['verified_artifact_bindings'][k] = sha(report)
save(recp, rec)
pfile = d/'PROGRESS_2026-10-13.json'
p = load(pfile)
p['candidate_artifacts']['cdd_result_report_sha256'] = sha(report)
p['candidate_artifacts']['cdd_dsh_disposition_sha256'] = sha(recp)
save(pfile, p)
mfile = d/'CDD_DELIVERABLE_HASHES_V1.json'
m = load(mfile)
m['files'] = {x.relative_to(root).as_posix():sha(x) for x in d.glob('*') if x.is_file() and x.name.startswith(('CDD_', 'run_shrink_cdd', 'audit_and_report_cdd', 'record_dsh', 'refresh_cdd_hashes', 'SHRINK_CDD', 'PROGRESS_')) and x != mfile}
m['reports'] = {x.relative_to(root).as_posix():sha(x) for x in [report, root/'docs/DRF_CDD_DSH_REVIEW_DISPOSITION_2026-10-13.md']}
save(mfile, m)
print('refreshed', sha(report), sha(recp), sha(pfile), sha(mfile))
