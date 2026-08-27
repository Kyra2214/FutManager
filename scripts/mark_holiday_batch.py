import json
from pathlib import Path
p=Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json'); d=json.loads(p.read_text())
e={'test':'brasfoot_engine/tests/test_p1_holiday_contract.py::test_holiday_contract_is_idempotent_and_protected','validation':'1 passed; py_compile; gateway argparse action present','source_of_truth':'SQL_GAMESTATE'}
for x in d['items']:
 if 1851<=int(x['item_id'])<=1860: x['status']='DONE'; x['evidence']=e
s=d['summary']; s['done']=sum(x.get('status')=='DONE' for x in d['items']); s['pending']=len(d['items'])-s['done']; p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n'); print(s)
