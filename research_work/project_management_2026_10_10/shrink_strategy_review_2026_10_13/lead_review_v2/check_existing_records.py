"""Read existing public summaries only; no model imports, fitting or private data."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = HERE.parent
PM = ROOT / 'research_work/project_management_2026_10_10'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def write_new(name, value):
    with (HERE/name).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

checked = []
for row in read(BASE/'DELIVERABLE_HASHES_V1.json')['files']:
    p = BASE / row['path']
    assert sha(p) == row['sha256'], str(p)
    checked.append(row['path'])
shrink_path = PM/'shrink_exploration_2026_10_13/CDD_SHRINK_EXPLORATORY_RESULTS_V1_1.json'
comp_path = PM/'compression_pilot_2026_10_13/RESULTS_V1.json'
assert sha(shrink_path) == 'dd8017676a0ccfe64bb4ab4bcf6ab81e477d183f2495377900049249b03883f5'
assert sha(comp_path) == 'e9f6583723bb5049b1956dc106e2c131c4224d8d67ec31cf5d11d31e8015ee79'
s, c = read(shrink_path), read(comp_path)
conditions = {}
rows = []
for r in s['runs']:
    f = r['fit']
    key = (r['asset'], r['fraction'])
    old = conditions.setdefault(key, f['ridge_lambda'])
    assert old == f['ridge_lambda']
    rows.append(dict(asset=r['asset'], fraction=r['fraction'], seed=r['seed'],
                     best_step=f['best_step'], ridge_lambda=f['ridge_lambda'],
                     validation_F_MSE_over_P=f['validation_mse']['F']/f['validation_mse']['P'],
                     validation_L_MSE_over_P=f['validation_mse']['L']/f['validation_mse']['P']))
arms = []
for a in c['arms']:
    h = {r['step']: r['validation_normalized_MSE'] for r in a['history']}
    arms.append(dict(arm=a['arm'], best_step=a['best_step'], ridge_lambda=a['ridge_lambda'],
                     validation_F_MSE_over_P=a['mse']['F']/a['mse']['P'],
                     validation_L_MSE_over_P=a['mse']['L']/a['mse']['P'],
                     mse_reduction_300_to_600_pct=100*(1-h[600]/h[300]),
                     minimum_legacy_ridge_lambda=0.001))
out = dict(scope='Arithmetic on existing result summaries; not independent array/checkpoint audit',
           repository=str(ROOT), head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
           verified_v1_deliverables=checked, shrink_F_fits=len(rows),
           shrink_best_at_budget_end=sum(r['best_step']==600 for r in rows),
           unique_legacy_ridge_conditions=len(conditions),
           unique_ridge_at_lower_grid_edge=sum(v==0.001 for v in conditions.values()),
           shrink_rows=rows, compression_arms=arms,
           new_training_fits=0, private_arrays_read=0)
write_new('RECORD_CHECKS.json', out)
inputs = [shrink_path, comp_path, BASE/'BRIEF_V1.md', BASE/'DELIVERABLE_HASHES_V1.json',
          BASE/'independent_review_v1/REVIEW.md', BASE/'independent_review_v1/NEXT_STEP_PLAN.md',
          ROOT/'docs/DRF_SMALL_PANEL_PLAN_V0.1_2026-10-06.md',
          ROOT/'research_work/forward_increment/qwen01_main/TEACHER_DECISION_BRIEF.md',
          ROOT/'docs/DRF_CDD_ETH_COMPRESSION_MINIMAL_PILOT_2026-10-13.md',
          PM/'compression_pilot_2026_10_13/PROTOCOL_V1.json',
          PM/'compression_pilot_2026_10_13/run_pilot_v1.py',
          PM/'compression_pilot_2026_10_13/audit_and_report_v1.py',
          PM/'shrink_exploration_2026_10_13/run_shrink_cdd_v1_1.py',
          PM/'compression_followup_2026_10_13/PROTOCOL_V0.1-DRAFT.json',
          ROOT/'models/derefusion/bundle_v3_pin/DeReFusion.py',
          ROOT/'models/derefusion/bundle_v3_pin/derefusion_components.py',
          ROOT/'models/derefusion/bundle_v3_pin/RevIN.py',
          ROOT/'reproduction/preprocessing/fixed_ohlc.py']
write_new('INPUT_HASHES.json',dict(head=out['head'], files=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in inputs]))
print(json.dumps({k:v for k,v in out.items() if k not in ('shrink_rows','verified_v1_deliverables')},ensure_ascii=False))
