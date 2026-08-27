from __future__ import annotations
import json
from pathlib import Path

manifest = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
payload = json.loads(manifest.read_text(encoding='utf-8'))
assert payload['gates']['P0_GLOBAL_GATE'] == 'OPEN'
refs = [
    ['brasfoot_engine/engine/manager/career.py:ensure_schema_version'],
    ['brasfoot_engine/engine/manager/career.py:SCHEMA', 'scripts/validate_3000_roadmap.py'],
    ['brasfoot_engine/engine/manager/career.py:migration_audit'],
    ['server/careerGateway.ts', 'server/routers/career.ts'],
    ['brasfoot_engine/engine/manager/career.py:assert_mutable_state_path'],
    ['brasfoot_engine/engine/manager/career.py:migration_audit', 'docs/relatorio_qualidade_entrega.md'],
    ['brasfoot_engine/engine/manager/career.py:indexes', 'tests/test_parallel_career_league.py'],
    ['server/careerGateway.test.ts', 'server/careerRouter.integration.test.ts'],
    ['docs/regras_fluxo_liga_unica_e_catalogo_paises.md'],
    ['server/CareerStart.ui.test.tsx', 'tests/test_parallel_career_league.py'],
]
for offset, evidence in enumerate(refs):
    item_id = 951 + offset
    item = next(item for item in payload['items'] if item['item_id'] == item_id)
    if item['priority'] != 'P1':
        raise RuntimeError(f'item {item_id} is not P1')
    item['status'] = 'DONE'
    item['evidence'] = evidence
payload['summary']['done'] = sum(item['status'] == 'DONE' for item in payload['items'])
payload['summary']['pending'] = sum(item['status'] == 'PENDING' for item in payload['items'])
payload['gates']['P0_GLOBAL_GATE'] = 'OPEN' if all(item['status'] == 'DONE' for item in payload['items'] if item['priority'] == 'P0') else 'CLOSED'
payload['gates']['P1_GLOBAL_GATE'] = 'OPEN' if payload['gates']['P0_GLOBAL_GATE'] == 'OPEN' and all(item['status'] == 'DONE' for item in payload['items'] if item['priority'] == 'P1') else 'CLOSED'
manifest.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': 'VALID', 'completed_batch': '951-960', 'done': payload['summary']['done'], 'pending': payload['summary']['pending'], 'gates': payload['gates']}, ensure_ascii=False))
