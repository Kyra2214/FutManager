from __future__ import annotations
import json
from pathlib import Path

manifest_path = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
payload = json.loads(manifest_path.read_text(encoding='utf-8'))
evidence = {
    941: ['brasfoot_engine/engine/manager/career.py:SCHEMA'],
    942: ['brasfoot_engine/tests/test_parallel_career_league.py', 'server/CareerStart.ui.test.tsx'],
    943: ['brasfoot_engine/engine/manager/career.py:ManagerService.__init__'],
    944: ['server/careerGateway.ts', 'server/routers/career.ts'],
    945: ['brasfoot_engine/engine/manager/career.py:_audit_permission'],
    946: ['docs/regras_fluxo_liga_unica_e_catalogo_paises.md'],
    947: ['brasfoot_engine/engine/manager/career.py:career_parallel_standings indexes'],
    948: ['brasfoot_engine/tests/test_parallel_career_league.py'],
    949: ['docs/regras_fluxo_liga_unica_e_catalogo_paises.md'],
    950: ['server/CareerStart.ui.test.tsx', 'server/careerRouter.integration.test.ts'],
}
items = {item['item_id']: item for item in payload['items']}
for item_id, refs in evidence.items():
    item = items[item_id]
    if item['priority'] != 'P0':
        raise RuntimeError(f'{item_id} is not P0')
    item['status'] = 'DONE'
    item['evidence'] = refs
payload['items'] = [items[item['item_id']] for item in payload['items']]
payload['summary']['done'] = sum(item['status'] == 'DONE' for item in payload['items'])
payload['summary']['pending'] = sum(item['status'] == 'PENDING' for item in payload['items'])
payload['gates']['P0_GLOBAL_GATE'] = 'OPEN' if all(item['status'] == 'DONE' for item in payload['items'] if item['priority'] == 'P0') else 'CLOSED'
payload['gates']['P1_GLOBAL_GATE'] = 'OPEN' if payload['gates']['P0_GLOBAL_GATE'] == 'OPEN' and all(item['status'] == 'DONE' for item in payload['items'] if item['priority'] == 'P1') else 'CLOSED'
manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': payload['status'], 'completed_batch': '941-950', 'done': payload['summary']['done'], 'pending': payload['summary']['pending'], 'gates': payload['gates']}, ensure_ascii=False))
