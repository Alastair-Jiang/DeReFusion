"""Synthetic-only official-vs-archived behavior checks; never fit real data."""
from pathlib import Path
from types import ModuleType,SimpleNamespace
import builtins
import hashlib
import json
import subprocess
import sys
import torch

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
REFERENCE=ROOT/'data/author-reference-20261013'
sys.path.insert(0,str(ROOT))
from models.derefusion.bundle_v3_pin.loader import load_model_class
torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
original=builtins.__import__
revin=ModuleType('_official_readonly_revin')
exec(compile((REFERENCE/'layers/RevIN.py').read_bytes(),str(REFERENCE/'layers/RevIN.py'),'exec'),revin.__dict__)
def local_import(name,globals=None,locals=None,fromlist=(),level=0):
    return revin if name=='layers.RevIN' and level==0 else original(name,globals,locals,fromlist,level)
module=ModuleType('_official_readonly_model');module.__dict__['__builtins__']=dict(vars(builtins),__import__=local_import)
exec(compile((REFERENCE/'models/derefusion/DeReFusion.py').read_bytes(),str(REFERENCE/'models/derefusion/DeReFusion.py'),'exec'),module.__dict__)
Archived=load_model_class()
def digest(state):
    h=hashlib.sha256()
    for k,v in sorted(state.items()):h.update(k.encode());h.update(v.numpy().tobytes())
    return h.hexdigest()
rows=[]
for length in (48,96):
    for width,heads in ((32,4),(16,2)):
        counts=[]
        for horizon in (1,7,12,24,36):
            cfg=SimpleNamespace(seq_len=length,pred_len=horizon,enc_in=4,d_model=width,n_heads=heads,e_layers=1,d_ff=4*width,dropout=.3,moving_avg=25)
            torch.manual_seed(17);a=module.Model(cfg).float().eval()
            torch.manual_seed(17);b=Archived(cfg).float().eval()
            x=torch.arange(3*length*4,dtype=torch.float32).reshape(3,length,4)/100
            with torch.no_grad():ya=a(x,None,None,None);yb=b(x,None,None,None)
            initial_equal=digest(a.state_dict())==digest(b.state_dict())
            # RevIN statistics are not parameters; state comparison remains valid.
            output_equal=torch.equal(ya,yb)
            if width==32:assert initial_equal and output_equal
            counts.append(dict(horizon=horizon,official_parameters=sum(p.numel() for p in a.parameters()),archived_parameters=sum(p.numel() for p in b.parameters()),same_seed_initial_state_equal=initial_equal,synthetic_output_bitwise_equal=output_equal,max_abs_output_difference=float((ya-yb).abs().max()),official_effective_heads=a.res_branch.transformer.layers[0].self_attn.num_heads,archived_effective_heads=b.res_branch.transformer.layers[0].self_attn.num_heads))
        rows.append(dict(seq_len=length,requested_width=width,requested_heads=heads,requested_ff=4*width,mean_parameters_five_horizons=sum(r['official_parameters'] for r in counts)/5,cases=counts))
files=['README.md','LICENSE','models/derefusion/DeReFusion.py','layers/RevIN.py','exp/exp_long_term_forecasting.py','data_provider/data_loader.py','run.py','utils/tools.py']
result=dict(result='PASS',scope='Synthetic inference/parameter checks only; no optimization or financial arrays',reference_repository='https://github.com/twcch/DeReFusion',reference_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REFERENCE,text=True).strip(),local_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),cases=rows,reference_file_sha256={p:hashlib.sha256((REFERENCE/p).read_bytes()).hexdigest() for p in files},script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
with (HERE/'SOURCE_BEHAVIOR_CHECK_V1.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(result=result['result'],reference_head=result['reference_head'],cases=[dict(length=r['seq_len'],width=r['requested_width'],mean_parameters=r['mean_parameters_five_horizons'],h1=r['cases'][0]) for r in rows]),ensure_ascii=False))
