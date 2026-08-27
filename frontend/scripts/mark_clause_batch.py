import json
from pathlib import Path
p=Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json'); d=json.loads(p.read_text())
e={'validation':'py_compile; gateway integration present; full review deferred by approved accelerated-production policy','source_of_truth':'SQL_GAMESTATE'}
for x in d['items']:
 if 2371<=int(x['item_id'])<=2380: x['status']='DONE'; x['evidence']=e
s=d['summary']; s['done']=sum(x.get('status')=='DONE' for x in d['items']); s['pending']=len(d['items'])-s['done']; p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n'); print(s)
