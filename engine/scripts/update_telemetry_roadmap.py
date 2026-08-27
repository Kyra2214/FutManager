from __future__ import annotations

import json
from pathlib import Path

path = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')
data = json.loads(path.read_text(encoding='utf-8'))
evidence = [
    'brasfoot_engine/engine/core/p1_telemetry_contract.py',
    'brasfoot_engine/engine/manager/career.py',
    'brasfoot_engine/scripts/career_gateway.py',
    'brasfoot_engine/tests/test_p1_telemetry_contract.py',
    'docs/p1_telemetry_1111_1120.md',
]
for item in data['items']:
    if 1111 <= item['item_id'] <= 1120:
        item['status'] = 'DONE'
        item['evidence'] = evidence
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('updated', sum(1 for item in data['items'] if 1111 <= item['item_id'] <= 1120 and item['status'] == 'DONE'))
