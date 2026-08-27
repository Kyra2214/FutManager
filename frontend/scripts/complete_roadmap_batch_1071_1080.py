from __future__ import annotations

import json
from pathlib import Path

manifest = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
evidence = ['brasfoot_engine/engine/core/p1_version_contract.py', 'brasfoot_engine/engine/manager/career.py', 'brasfoot_engine/scripts/career_gateway.py', 'brasfoot_engine/tests/test_p1_version_contract.py', 'docs/p1_version_1071_1080.md']
payload = json.loads(manifest.read_text(encoding='utf-8'))
assert payload['gates']['P0_GLOBAL_GATE'] == 'OPEN'
items = payload['items']
batch = [item for item in items if 1071 <= item['item_id'] <= 1080]
assert len(batch) == 10 and all(item['priority'] == 'P1' and item['status'] == 'PENDING' for item in batch)
for item in batch:
    item['status'] = 'DONE'
    item['evidence'] = evidence
payload['summary']['done'] = sum(item['status'] == 'DONE' for item in items)
payload['summary']['pending'] = sum(item['status'] == 'PENDING' for item in items)
payload['gates']['P1_GLOBAL_GATE'] = 'OPEN' if all(item['status'] == 'DONE' for item in items if item['priority'] == 'P1') else 'CLOSED'
assert payload['gates']['P1_GLOBAL_GATE'] == 'CLOSED'
manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': 'VALID', 'batch': '1071-1080', 'completed': 10, 'done': payload['summary']['done'], 'pending': payload['summary']['pending'], 'gates': payload['gates']}, ensure_ascii=False))
