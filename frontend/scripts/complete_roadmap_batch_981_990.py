from __future__ import annotations
import json
from pathlib import Path

MANIFEST = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
payload = json.loads(MANIFEST.read_text(encoding='utf-8'))
completed = [item['item_id'] for item in payload['items'] if item['status'] == 'DONE']
assert completed == list(range(941, 981))
refs = [
    ['brasfoot_engine/engine/manager/career.py:create_backup_manifest'],
    ['brasfoot_engine/tests/test_parallel_career_league.py:test_backup_manifest_is_deterministic_and_idempotent'],
    ['brasfoot_engine/engine/manager/career.py:career_backup_manifests'],
    ['brasfoot_engine/engine/manager/career.py:list_backup_manifests'],
    ['brasfoot_engine/engine/manager/career.py:assert_mutable_state_path'],
    ['brasfoot_engine/engine/manager/career.py:create_backup_manifest'],
    ['brasfoot_engine/engine/manager/career.py:idx_world_countries_career'],
    ['brasfoot_engine/tests/test_parallel_career_league.py'],
    ['docs/procedimento_recuperacao_checkpoint.md'],
    ['brasfoot_engine/tests/test_parallel_career_league.py:test_backup_manifest_is_deterministic_and_idempotent'],
]
for offset, evidence in enumerate(refs):
    item = next(item for item in payload['items'] if item['item_id'] == 981 + offset)
    assert item['priority'] == 'P1'
    item['status'] = 'DONE'
    item['evidence'] = evidence
payload['summary']['done'] = sum(item['status'] == 'DONE' for item in payload['items'])
payload['summary']['pending'] = sum(item['status'] == 'PENDING' for item in payload['items'])
payload['gates']['P0_GLOBAL_GATE'] = 'OPEN' if all(item['status'] == 'DONE' for item in payload['items'] if item['priority'] == 'P0') else 'CLOSED'
payload['gates']['P1_GLOBAL_GATE'] = 'OPEN' if payload['gates']['P0_GLOBAL_GATE'] == 'OPEN' and all(item['status'] == 'DONE' for item in payload['items'] if item['priority'] == 'P1') else 'CLOSED'
MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status': 'VALID', 'completed_batch': '981-990', 'done': payload['summary']['done'], 'pending': payload['summary']['pending'], 'gates': payload['gates']}, ensure_ascii=False))
