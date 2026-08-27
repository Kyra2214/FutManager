from pathlib import Path
import json
p=Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
d=json.loads(p.read_text())
e=['brasfoot_engine/engine/core/p1_revocation_contract.py','brasfoot_engine/engine/manager/career.py','brasfoot_engine/scripts/career_gateway.py','brasfoot_engine/tests/test_p1_revocation_contract.py','docs/p1_revocation_1191_1200.md']
for x in d['items']:
 if 1191<=x['item_id']<=1200: x['status']='DONE'; x['evidence']=e
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('updated',sum(x['status']=='DONE' for x in d['items'] if 1191<=x['item_id']<=1200))
