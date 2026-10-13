"""Enforce the declared one-process wall-clock cap and retain dispatch failures."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
review=json.loads((HERE/'ENGINEERING_REVIEW_V1.json').read_text(encoding='utf-8-sig'))
assert review['result']=='PASS'
assert review['code_sha256']==sha(HERE/'run_oos.py')
assert review['protocol_sha256']==sha(HERE/'PROTOCOL_V1.json')
assert review['controller_sha256']==sha(Path(__file__))
start=time.monotonic()
try:
    proc=subprocess.run([sys.executable,'-B',str(HERE/'run_oos.py'),'evaluate'],cwd=HERE.parents[2],capture_output=True,text=True,timeout=300)
    if proc.returncode:raise RuntimeError(proc.stderr[-3000:])
    print(proc.stdout,end='')
    result={'result':'PASS','seconds':time.monotonic()-start,'limit_seconds':300,'controller_sha256':sha(Path(__file__))}
except Exception as exc:
    result={'result':'FAIL','reason':str(exc),'type':type(exc).__name__,'seconds':time.monotonic()-start,'controller_sha256':sha(Path(__file__))}
    name='DISPATCH_FAILURE_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json'
    with (HERE/name).open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    raise
with (HERE/'DISPATCH_RECEIPT_V1.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
