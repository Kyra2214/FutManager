from __future__ import annotations
import json
from pathlib import Path

MANIFEST = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
payload = json.loads(MANIFEST.read_text(encoding='utf-8'))
assert payload['gates']['P0_GLOBAL_GATE'] == 'OPEN'
refs = [
    ['brasfoot_engine/engine/manager/career.py:audit_constraints'],
    ['brasfoot_engine/tests/test_parallel_career_league.py:test_constraint_audit_is_read_only_and_validates_parallel_state'],
    ['brasfoot_engine/engine/manager/career.py:PRAGMA integrity_check'],
    ['brasfoot_engine/engine/manager/career.py:PRAGMA foreign_key_check'],
    ['brasfoot_engine/engine/manager/career.py:audit_constraints', 'server/careerGateway.ts'],
    ['brasfoot_engine/tests/test_parallel_career_league.py'],
    ['brasfoot_engine/engine/manager/career.py:PRIMARY KEY and UNIQUE constraints'],
    ['brasfoot_engine/tests/test_parallel_career_league.py:read-only audit'],
    ['docs/regras_fluxo_liga_unica_e_catalogo_paises.md'],
    ['brasfoot_engine/tests/test_parallel_career_league.py', 'server/CareerStart.ui.test.tsx'],
]
for offset, evidence in enumerate(refs):
    item = next(item for item in payload['items'] if item['item_id'] == 961 + offset)
    assert item['priority'] == 'P1'
    item['status'] = 'DONE'
    item['evidence'] = evidence
payload['summary']['done'] = sum(item['status'] == 'DONE' for item in payload['items'])
payload['summary']['pending'] = sum(item['status'] == 'PENDING' for item in payload['items'])
payload['gates']['P0_GLOBAL_GATE'] = 'OPEN' if all(item['status'] == 'DONE' for item in payload['items'] if item['priority'] == 'P0') else 'CLOSED'
payload['gates']['P1_GLOBAL_GATE'] = 'OPEN' if payload['gates']['P0_GLOBAL_GATE'] == 'OPEN' and all(item['status'] == 'DONE' for item in payload['items'] if item['priority'] == 'P1') else 'CLOSED'
MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': 'VALID', 'completed_batch': '961-970', 'done': payload['summary']['done'], 'pending': payload['summary']['pending'], 'gates': payload['gates']}, ensure_ascii=False))
