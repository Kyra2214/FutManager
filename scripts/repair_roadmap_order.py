from __future__ import annotations
import json
from pathlib import Path

manifest = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
payload = json.loads(manifest.read_text(encoding='utf-8'))
allowed = set(range(941, 981))
for item in payload['items']:
    if item['status'] == 'DONE' and item['item_id'] not in allowed:
        item['status'] = 'PENDING'
        item['evidence'] = []
payload['summary']['done'] = sum(item['status'] == 'DONE' for item in payload['items'])
payload['summary']['pending'] = sum(item['status'] == 'PENDING' for item in payload['items'])
payload['gates']['P0_GLOBAL_GATE'] = 'CLOSED'
payload['gates']['P1_GLOBAL_GATE'] = 'CLOSED'
payload['notes'] = 'Order repaired: only the sequential prefix 941-980 is allowed to remain completed.'
manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': 'VALID', 'done': payload['summary']['done'], 'pending': payload['summary']['pending'], 'last_done': max(item['item_id'] for item in payload['items'] if item['status'] == 'DONE'), 'gates': payload['gates']}, ensure_ascii=False))
