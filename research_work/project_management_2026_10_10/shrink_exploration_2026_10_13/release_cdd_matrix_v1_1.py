"""Issue the narrowly scoped execution release after identity/QA/synthetic checks."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PRIVATE=ROOT/'data/shrink-cdd-20261013-v1'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    protocol=HERE/'SHRINK_CDD_EXPLORATORY_PROTOCOL_V0.2.json'
    runner=HERE/'run_shrink_cdd_v1_1.py'
    prep=HERE/'CDD_PREPARATION_MANIFEST_V1_1.json'
    synth=HERE/'CDD_MATRIX_SYNTHETIC_CHECK_V1_1.json'
    output=HERE/'CDD_MATRIX_EXECUTION_RELEASE_V1_1.json'
    if output.exists(): raise ValueError('Release already exists; no overwrite')
    p=json.loads(protocol.read_text(encoding='utf-8'))
    preparation=json.loads(prep.read_text(encoding='utf-8'))
    synthetic=json.loads(synth.read_text(encoding='utf-8'))
    if preparation['result']!='PASS' or synthetic['result']!='PASS': raise ValueError('Checks not passed')
    for record in [preparation,synthetic]:
        if record['runner_sha256']!=sha(runner) or record['protocol_sha256']!=sha(protocol): raise ValueError('Evidence drift')
    for asset,expected in p['raw_sha256'].items():
        if sha(PRIVATE/(asset+'.raw.csv'))!=expected: raise ValueError('Raw data drift')
    for row in preparation['combinations']:
        for package in row['packages'].values():
            if sha(Path(package['path']))!=package['sha256']: raise ValueError('Package drift')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    if head!='a74126c11d857da8514074b72282adc8d47f28a7': raise ValueError('HEAD drift')
    diff=subprocess.check_output(['git','diff','--binary'],cwd=ROOT)
    untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=ROOT)
    stamp=datetime.now(timezone.utc).isoformat()
    record={'release_id':'DRF-SHRINK-CDD-MATRIX-20261013-V1.1','decision':'APPROVED',
            'decision_owner':'Codex under explicit project-lead delegation; user prioritizes startup with adequate permission or alternative source',
            'decided_at_utc':stamp,'repository':str(ROOT),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip(),
            'head':head,'tracked_diff_sha256':hashlib.sha256(diff).hexdigest(),
            'untracked_path_inventory_sha256':hashlib.sha256(untracked).hexdigest(),
            'protocol_id':p['protocol_id'],'protocol_sha256':sha(protocol),'runner_sha256':sha(runner),
            'preparation_sha256':sha(prep),'synthetic_sha256':sha(synth),
            'source_sha256':p['model']['source_sha256'],'raw_sha256':p['raw_sha256'],
            'qualification_release_sha256':sha(HERE/'CDD_LOCAL_RESEARCH_QUALIFICATION_RELEASE_V1.json'),
            'scope':'New CDD Bitstamp BTC/USD and ETH/USD; internal local non-commercial exploratory fits, validation selection and private evaluation',
            'input_root':str(PRIVATE/'packages_v1_1'),'output_root':str(PRIVATE/'runs_v1_1'),
            'worker_access':'Fit takes only train+validation package paths. Evaluator gets test after all fits and validation roster freeze. T0 discipline, not OS security.',
            'budget':p['budget'],'torch':'2.5.1+cpu','paid_cost':0,
            'planned_F_fits':24,'planned_ridge_unique_conditions':8,'planned_optimizer_steps':14400,
            'forbidden':'No processing of old Yahoo files; no public raw data/predictions/weights/commercial use; no confirmation claims',
            'stops':p['failure_policy'],
            'repair_record':'v1 preparation wrote eight packages but could not serialize a NumPy integer in metadata. Preserve failed packages and v1 synthetic report. v1.1 casts metadata integer, adds synthetic metadata-serialization check, creates a fresh package/output root; no scientific configuration changed.'}
    output.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    progress_path=HERE/'PROGRESS_2026-10-13.json'
    progress=json.loads(progress_path.read_text(encoding='utf-8-sig'))
    progress['legacy_source_gate']={'scope':'Original Yahoo-labelled BTCUSD/ETHUSD/GSPC/N225 files','state':'UNRESOLVED; do not process or infer retroactive permission'}
    progress['active_protocol_id']=p['protocol_id']
    progress['status']='REAL_DATA_QUALIFIED_MATRIX_RELEASED_PENDING_FITS'
    progress['last_updated_local']=datetime.now().astimezone().isoformat()
    progress['active_counts']={'planned_F_fits':24,'completed_F_fits':0,'audited_F_fits':0,'unique_history_conditions':8,'qualified_assets':2}
    for key,path in [('cdd_qualification',HERE/'CDD_QUALIFICATION_RESULTS_V1.json'),('cdd_protocol',protocol),('cdd_runner',runner),('cdd_preparation',prep),('cdd_synthetic',synth),('cdd_execution_release',output)]:
        progress['candidate_artifacts'][key]=str(path.relative_to(ROOT)).replace('\\','/')
        progress['candidate_artifacts'][key+'_sha256']=sha(path)
    progress['gates']=[
        {'id':'G0','state':'CLEARED_FOR_NEW_CDD_BTC_ETH_ONLY','evidence':'Official supplier affirmative non-commercial research offering and automatable CSV download route, snapshots hashed; bounded internal basis accepted; old Yahoo source remains unresolved'},
        {'id':'G1','state':'FROZEN_FOR_V0.2','evidence':'Protocol fixes target/grid/splits/retained contexts/common keys/baselines/seeds/600 steps/checkpoint/rank/budget/failure rules'},
        {'id':'G2','state':'RELEASED_V1.1','evidence':'QA PASS, eight prepared conditions, matrix-specific synthetic PASS, exact runner/data/key/source pins checked'},
        {'id':'G3','state':'READY_NOT_YET_STARTED','evidence':'24 F fits planned; start only from the exact v1.1 released runner'}]
    for track in progress['tracks'].values():
        track['state']='RELEASED_FOR_NEW_CDD_TWO_ASSET_PROTOCOL'
        track['run_authorized']=True
        track['assets']=['BTCUSD','ETHUSD']
    progress['latest_actions'] += ['Accepted a scoped local non-commercial research basis for new CDD Bitstamp BTC/ETH using official research/terms/automated-download pages; no request for signed vendor permission.',
                                  'Downloaded two new-source CSVs into an already gitignored directory; QA PASS, 2922 complete 2018-2025 daily keys each. Old Yahoo inputs untouched.',
                                  'Fixed a preparation metadata serialization error in a retained v1.1 successor; synthetic checks and eight fresh role-package combinations PASS.',
                                  'Issued exact-pinned execution release for 24 exploratory F fits (600 steps each), deterministic ridge/persistence comparisons, and a validation-frozen two-asset screen.']
    progress_path.write_text(json.dumps(progress,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'decision':'APPROVED','release':str(output),'release_sha256':sha(output),'planned_F_fits':24}))
if __name__=='__main__': main()
