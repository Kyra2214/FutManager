from __future__ import annotations
import json
from pathlib import Path
path=Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
data=json.loads(path.read_text(encoding='utf-8'))
evidence=['brasfoot_engine/engine/core/p1_role_contract.py','brasfoot_engine/engine/manager/career.py','brasfoot_engine/scripts/career_gateway.py','brasfoot_engine/tests/test_p1_session_contract.py','docs/p1_role_1161_1170.md']
for item in data['items']:
    if 1161 <= item['item_id'] <= 1170:
        item['status']='DONE'; item['evidence']=evidence
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('updated',sum(1 for item in data['items'] if 1161<=item['item_id']<=1170 and item['status']=='DONE'))
