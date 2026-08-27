import json
from datetime import datetime, timezone
from pathlib import Path

path = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
data = json.loads(path.read_text(encoding='utf-8'))
evidence = {
    'test': 'brasfoot_engine/tests/test_p1_stadium_contract.py::test_stadium_contract_is_idempotent_and_protected',
    'validation': '1 passed; py_compile p1_stadium_contract.py career.py career_gateway.py',
    'source_of_truth': 'SQL_GAMESTATE',
}
for item in data['items']:
    if 1301 <= int(item['item_id']) <= 1310:
        item['status'] = 'DONE'
        item['evidence'] = evidence
summary = data.setdefault('summary', {})
summary['done'] = sum(1 for item in data['items'] if item.get('status') == 'DONE')
summary['pending'] = len(data['items']) - summary['done']
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'batch': '1301-1310', 'done': summary['done'], 'pending': summary['pending']}, ensure_ascii=False))
