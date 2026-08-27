from __future__ import annotations
import json
from pathlib import Path

MANIFEST = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
payload = json.loads(MANIFEST.read_text(encoding='utf-8'))
assert payload['gates']['P0_GLOBAL_GATE'] == 'OPEN'
refs = [
    ['brasfoot_engine/engine/manager/career.py:idx_parallel_fixtures_lookup'],
    ['brasfoot_engine/engine/manager/career.py:audit_indexes'],
    ['brasfoot_engine/engine/manager/career.py:CREATE INDEX IF NOT EXISTS'],
    ['brasfoot_engine/engine/manager/career.py:audit_indexes'],
    ['brasfoot_engine/engine/manager/career.py:read-only index audit'],
    ['brasfoot_engine/engine/manager/career.py:EXPLAIN QUERY PLAN'],
    ['brasfoot_engine/tests/test_parallel_career_league.py:test_index_audit_confirms_calendar_and_standings_plans'],
    ['brasfoot_engine/tests/test_parallel_career_league.py'],
    ['docs/regras_fluxo_liga_unica_e_catalogo_paises.md'],
    ['brasfoot_engine/tests/test_parallel_career_league.py', 'server/careerGateway.test.ts'],
]
for offset, evidence in enumerate(refs):
    item = next(item for item in payload['items'] if item['item_id'] == 971 + offset)
    assert item['priority'] == 'P1'
    item['status'] = 'DONE'
    item['evidence'] = evidence
payload['summary']['done'] = sum(item['status'] == 'DONE' for item in payload['items'])
payload['summary']['pending'] = sum(item['status'] == 'PENDING' for item in payload['items'])
payload['gates']['P0_GLOBAL_GATE'] = 'OPEN' if all(item['status'] == 'DONE' for item in payload['items'] if item['priority'] == 'P0') else 'CLOSED'
payload['gates']['P1_GLOBAL_GATE'] = 'OPEN' if payload['gates']['P0_GLOBAL_GATE'] == 'OPEN' and all(item['status'] == 'DONE' for item in payload['items'] if item['priority'] == 'P1') else 'CLOSED'
MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': 'VALID', 'completed_batch': '971-980', 'done': payload['summary']['done'], 'pending': payload['summary']['pending'], 'gates': payload['gates']}, ensure_ascii=False))
