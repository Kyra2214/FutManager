from __future__ import annotations

import json
from pathlib import Path

MANIFEST = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
EVIDENCE = [
    'brasfoot_engine/engine/core/p1_procedure_contract.py',
    'brasfoot_engine/engine/manager/career.py',
    'brasfoot_engine/scripts/career_gateway.py',
    'brasfoot_engine/tests/test_p1_procedure_contract.py',
    'docs/p1_procedure_1051_1060.md',
]

payload = json.loads(MANIFEST.read_text(encoding='utf-8'))
assert payload['gates']['P0_GLOBAL_GATE'] == 'OPEN'
items = payload['items']
batch = [item for item in items if 1051 <= item['item_id'] <= 1060]
assert len(batch) == 10
assert all(item['priority'] == 'P1' for item in batch)
assert all(item['status'] == 'PENDING' for item in batch)
for item in batch:
    item['status'] = 'DONE'
    item['evidence'] = EVIDENCE
payload['summary']['done'] = sum(item['status'] == 'DONE' for item in items)
payload['summary']['pending'] = sum(item['status'] == 'PENDING' for item in items)
payload['gates']['P1_GLOBAL_GATE'] = 'OPEN' if all(item['status'] == 'DONE' for item in items if item['priority'] == 'P1') else 'CLOSED'
assert payload['gates']['P0_GLOBAL_GATE'] == 'OPEN'
assert payload['gates']['P1_GLOBAL_GATE'] == 'CLOSED'
MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': 'VALID', 'batch': '1051-1060', 'completed': len(batch), 'done': payload['summary']['done'], 'pending': payload['summary']['pending'], 'gates': payload['gates']}, ensure_ascii=False))
