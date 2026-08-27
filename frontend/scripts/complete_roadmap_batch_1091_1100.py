import json
from pathlib import Path
m=Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json'); p=json.loads(m.read_text())
assert p['gates']['P0_GLOBAL_GATE']=='OPEN'
b=[i for i in p['items'] if 1091<=i['item_id']<=1100]; assert len(b)==10 and all(i['priority']=='P1' and i['status']=='PENDING' for i in b)
e=['brasfoot_engine/engine/core/p1_domain_version_contract.py','brasfoot_engine/engine/manager/career.py','brasfoot_engine/scripts/career_gateway.py','brasfoot_engine/tests/test_p1_domain_version_contract.py','docs/p1_domain_version_1091_1100.md']
for i in b: i.update(status='DONE',evidence=e)
p['summary']['done']=sum(i['status']=='DONE' for i in p['items']); p['summary']['pending']=sum(i['status']=='PENDING' for i in p['items']); p['gates']['P1_GLOBAL_GATE']='OPEN' if all(i['status']=='DONE' for i in p['items'] if i['priority']=='P1') else 'CLOSED'; assert p['gates']['P1_GLOBAL_GATE']=='CLOSED'; m.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n'); print({'status':'VALID','batch':'1091-1100','done':p['summary']['done'],'pending':p['summary']['pending']})
