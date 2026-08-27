from pathlib import Path
import json
p=Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
d=json.loads(p.read_text())
for item in d['items']:
    if 1181 <= item['item_id'] <= 1190:
        item['status']='PENDING'
        item.pop('evidence',None)
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('reopened', sum(1 for x in d['items'] if 1181<=x['item_id']<=1190 and x['status']=='PENDING'))
