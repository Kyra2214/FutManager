from pathlib import Path
import json
import re

path = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_melhorias_941_3940.md')
text = path.read_text(encoding='utf-8')
items = []
for line in text.splitlines():
    match = re.match(r'^(\d+)\. \*\*\[(P[012])\] (.+?)\*\* — Dependência: `([^`]+)`\. Critério: (.+)\.$', line)
    if match:
        items.append({'id': int(match.group(1)), 'priority': match.group(2), 'title': match.group(3), 'dependency': match.group(4), 'criterion': match.group(5)})
ids = [item['id'] for item in items]
priorities = {key: sum(item['priority'] == key for item in items) for key in ('P0', 'P1', 'P2')}
result = {
    'status': 'VALID' if ids == list(range(941, 3941)) and len(set(ids)) == 3000 and priorities == {'P0': 300, 'P1': 2100, 'P2': 600} and all(item['dependency'] and item['criterion'] for item in items) else 'INVALID',
    'item_count': len(items),
    'first_id': ids[0] if ids else None,
    'last_id': ids[-1] if ids else None,
    'unique_id_count': len(set(ids)),
    'priority_counts': priorities,
    'items_with_dependency': sum(bool(item['dependency']) for item in items),
    'items_with_criterion': sum(bool(item['criterion']) for item in items),
}
out = Path('/home/ubuntu/futmanager_frontend/docs/validacao_roadmap_3000.json')
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
if result['status'] != 'VALID':
    raise SystemExit(1)
