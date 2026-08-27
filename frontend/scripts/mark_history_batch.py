import json
from pathlib import Path

path = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
data = json.loads(path.read_text(encoding='utf-8'))
evidence = {'test': 'brasfoot_engine/tests/test_p1_history_contract.py::test_history_contract_is_idempotent_and_protected', 'validation': '1 passed; py_compile; gateway argparse action present', 'source_of_truth': 'SQL_GAMESTATE'}
for item in data['items']:
    if 1411 <= int(item['item_id']) <= 1420:
        item['status'] = 'DONE'
        item['evidence'] = evidence
summary = data.setdefault('summary', {})
summary['done'] = sum(1 for item in data['items'] if item.get('status') == 'DONE')
summary['pending'] = len(data['items']) - summary['done']
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'batch': '1411-1420', 'done': summary['done'], 'pending': summary['pending']}))
