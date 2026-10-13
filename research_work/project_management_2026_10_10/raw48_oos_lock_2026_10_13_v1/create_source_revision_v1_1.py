"""Create a fresh repair attempt without modifying the failed protocol."""
from pathlib import Path
import hashlib
import json

OLD=Path(__file__).resolve().parent;ROOT=OLD.parents[2]
NEW=ROOT/'research_work/project_management_2026_10_10/raw48_oos_lock_2026_10_13_v1_1'
NEW.mkdir(exist_ok=False)
for name in ('run_oos.py','execute_bound.py','audit_and_report.py'):
    text=(OLD/name).read_text(encoding='utf-8')
    text=text.replace("ROOT/'data/raw48-oos-20261013-v1'","ROOT/'data/raw48-oos-20261013-v1-1'")
    text=text.replace("ROOT/'data/shrink-cdd-20261013-v1/ETHUSD.raw.csv'","ROOT/'data/raw48-oos-20261013-v1-1/QUALIFIED_INPUT.csv'")
    with (NEW/name).open('x',encoding='utf-8',newline='\n') as f:f.write(text)
p=json.loads((OLD/'PROTOCOL_V1.json').read_text(encoding='utf-8-sig'))
p['protocol_id']='DRF-RAW48-LOCKED-TEMPORAL-EVALUATION-20261013-V1.1'
p['status']='APPROVED_REPAIR_PREFLIGHT_ONLY_PENDING_NEW_RELEASE'
pins={}
for path,pin in p['input_sha256'].items():
    if path.endswith('/raw48_oos_lock_2026_10_13_v1/run_oos.py') or path=='data/shrink-cdd-20261013-v1/ETHUSD.raw.csv':continue
    pins[path]=pin
for path in [NEW/'run_oos.py',NEW/'execute_bound.py',Path(__file__),ROOT/'data/raw48-oos-20261013-v1-1/QUALIFIED_INPUT.csv',ROOT/'data/raw48-oos-source-check-20261013-v1/BITSTAMP_CONTEXT_OHLC_RESPONSE.json',OLD/'SOURCE_QUALIFICATION_RESULT_V1_1.json',OLD/'SOURCE_QUALIFICATION_AMENDMENT_V1_1.json',OLD/'BITSTAMP_METADATA_CHECK_RELEASE_V1.json',OLD/'PROTOCOL_V1.json',OLD/'COVERAGE_FAILURE_V1.json']:
    pins[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
p['input_sha256']=pins
p['source_revision']={'reason':'CDD missing2026-05-22; calendar QA stopped before inference','training':'Original CDD Bitstamp2018-2022 unchanged numerical values','context_evaluation':'Entire333-day span from official Bitstamp API, no interpolation/single-row patch','overlap':'331 of332 overlapping candles exact decimal OHLC;2026-05-21 differs; cause unknown, do not assert exact source equivalence','model_checkpoint_keys_and_comparisons':'Unchanged; no score-driven repair','old_attempt':'Preserved V1 failure, zero predictions/scores'}
p['data_use']='Explicit new bounded local non-commercial public Bitstamp API temporal research and original CDD train reconstruction under project delegation; external unrestricted/commercial/redistribution rights not asserted'
p['exposure']='V1 QA parsed2026 prices but stopped before inference; API qualification observed prices/coverage. No performance score produced for2026 before this lock; cross-agent exposure unknown; retrospective descriptive only'
with (NEW/'PROTOCOL_V1.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(p,f,ensure_ascii=False,indent=2);f.write('\n')
for name in ('PLAN_V1.md','EXPOSURE_REGISTER_V1.md'):
    text=(OLD/name).read_text(encoding='utf-8')
    text+='\n\n## V1.1 源数据修复\n\nV1在2026-05-22缺失时停止，未生成模型预测或分数。保留旧attempt，新协议改用官方Bitstamp API完整333天作为全部上下文/评价源，原CDD2018–2022训练/缩放数值不变。332重叠日中331的OHLC十进制相等，2026-05-21存在差异，原因未证；不得声称源完全等价。没有插值或只补一行；选择因日期资格失败而非模型分数，模型/seed/285键/主比较不变。原QA已解析2026及新API价格，因此只称历史锁定评价，不能称从未读取价格。新的执行必须经新协议hash、preflight、工程审查和释放。\n'
    with (NEW/name).open('x',encoding='utf-8',newline='\n') as f:f.write(text)
print('Created fresh V1.1 source revision; model and key locks unchanged')
