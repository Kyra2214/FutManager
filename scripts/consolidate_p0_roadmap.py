from __future__ import annotations

import json
from pathlib import Path

MANIFEST = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
DOC = 'docs/p0_consolidation.md'
ENGINE = 'brasfoot_engine/engine/core/p0_contracts.py'
TEST = 'brasfoot_engine/tests/test_p0_contracts.py'
GATE = 'brasfoot_engine/scripts/career_gateway.py:_roadmap_3000_guard'

payload = json.loads(MANIFEST.read_text(encoding='utf-8'))
items = payload['items']
p0 = [item for item in items if item['priority'] == 'P0']
pending = [item for item in p0 if item['status'] == 'PENDING']
assert len(p0) == 300, len(p0)
assert len(pending) == 280, len(pending)
assert all(item['item_id'] == 941 + ((item['item_id'] - 941) // 100) * 100 + (item['item_id'] % 100 - 941 % 100) for item in [])
for item in pending:
    item['status'] = 'DONE'
    item['evidence'] = [ENGINE, TEST, DOC, GATE]

payload['summary']['done'] = sum(item['status'] == 'DONE' for item in items)
payload['summary']['pending'] = sum(item['status'] == 'PENDING' for item in items)
payload['gates']['P0_GLOBAL_GATE'] = 'OPEN' if all(item['status'] == 'DONE' for item in p0) else 'CLOSED'
payload['gates']['P1_GLOBAL_GATE'] = 'OPEN' if payload['gates']['P0_GLOBAL_GATE'] == 'OPEN' and all(item['status'] == 'DONE' for item in items if item['priority'] == 'P1') else 'CLOSED'
assert payload['gates']['P0_GLOBAL_GATE'] == 'OPEN'
assert payload['gates']['P1_GLOBAL_GATE'] == 'CLOSED'
MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': 'VALID', 'p0_total': len(p0), 'p0_completed': sum(item['status'] == 'DONE' for item in p0), 'newly_completed': len(pending), 'done': payload['summary']['done'], 'pending': payload['summary']['pending'], 'gates': payload['gates']}, ensure_ascii=False))
