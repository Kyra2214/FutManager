from pathlib import Path
import json
p=Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
d=json.loads(p.read_text())
e=['brasfoot_engine/engine/core/p1_consent_contract.py','brasfoot_engine/engine/manager/career.py','brasfoot_engine/scripts/career_gateway.py','brasfoot_engine/tests/test_p1_consent_contract.py','docs/p1_consent_1211_1220.md']
for item in d['items']:
    if 1211 <= item['item_id'] <= 1220:
        item['status']='DONE'; item['evidence']=e
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('updated',sum(item['status']=='DONE' for item in d['items'] if 1211 <= item['item_id'] <= 1220))
