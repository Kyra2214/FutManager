from __future__ import annotations
import json
from pathlib import Path

manifest = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
data = json.loads(manifest.read_text(encoding='utf-8'))
completed = [item['item_id'] for item in data['items'] if item['status'] == 'DONE']
assert completed == list(range(941, 1021))
evidence = [
    ['brasfoot_engine/engine/core/payload_contract.py'],
    ['brasfoot_engine/tests/test_payload_contract_p0.py::test_payload_contract_rejects_invalid_shapes_and_size'],
    ['brasfoot_engine/engine/manager/career.py:career_journal'],
    ['brasfoot_engine/scripts/career_gateway.py:515-522'],
    ['brasfoot_engine/scripts/career_gateway.py:515-522', 'brasfoot_engine/tests/test_payload_contract_p0.py'],
    ['docs/payload_contract_p0.md', 'brasfoot_engine/tests/test_gateway_contracts_p0.py'],
    ['brasfoot_engine/engine/core/payload_contract.py:payload_fingerprint'],
    ['brasfoot_engine/tests/test_payload_contract_p0.py::test_gateway_emits_payload_fingerprint_and_stable_error'],
    ['docs/payload_contract_p0.md'],
    ['brasfoot_engine/tests/test_payload_contract_p0.py', 'server/careerGateway.test.ts'],
]
for idx, refs in enumerate(evidence, 1041):
    item = next(item for item in data['items'] if item['item_id'] == idx)
    assert item['status'] == 'PENDING' and item['priority'] == 'P0'
    item['status'] = 'DONE'
    item['evidence'] = refs
data['summary']['done'] = sum(item['status'] == 'DONE' for item in data['items'])
data['summary']['pending'] = sum(item['status'] == 'PENDING' for item in data['items'])
data['gates']['P0_GLOBAL_GATE'] = 'OPEN' if all(item['status'] == 'DONE' for item in data['items'] if item['priority'] == 'P0') else 'CLOSED'
data['gates']['P1_GLOBAL_GATE'] = 'OPEN' if data['gates']['P0_GLOBAL_GATE'] == 'OPEN' and all(item['status'] == 'DONE' for item in data['items'] if item['priority'] == 'P1') else 'CLOSED'
manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'status':'VALID','batch':'1041-1050','done':data['summary']['done'],'pending':data['summary']['pending'],'gates':data['gates']}, ensure_ascii=False))
