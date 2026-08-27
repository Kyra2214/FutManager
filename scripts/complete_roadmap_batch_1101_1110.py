import json
from pathlib import Path
m=Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json'); p=json.loads(m.read_text())
assert p['gates']['P0_GLOBAL_GATE']=='OPEN'
b=[i for i in p['items'] if 1101<=i['item_id']<=1110]; assert len(b)==10 and all(i['priority']=='P1' and i['status']=='PENDING' for i in b)
e=['brasfoot_engine/engine/core/p1_timeout_contract.py','brasfoot_engine/engine/manager/career.py','brasfoot_engine/scripts/career_gateway.py','brasfoot_engine/tests/test_p1_timeout_contract.py','docs/p1_timeout_1101_1110.md']
for i in b: i.update(status='DONE',evidence=e)
p['summary']['done']=sum(i['status']=='DONE' for i in p['items']); p['summary']['pending']=sum(i['status']=='PENDING' for i in p['items']); p['gates']['P1_GLOBAL_GATE']='OPEN' if all(i['status']=='DONE' for i in p['items'] if i['priority']=='P1') else 'CLOSED'; assert p['gates']['P1_GLOBAL_GATE']=='CLOSED'; m.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n'); print({'status':'VALID','batch':'1101-1110','done':p['summary']['done'],'pending':p['summary']['pending']})
