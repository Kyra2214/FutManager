from __future__ import annotations

import json
import re
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'docs' / 'novas_200_implementacoes_501_700.md'
text = path.read_text(encoding='utf-8')
rows = []
for line in text.splitlines():
    match = re.match(r'^\|\s*(\d+)\s*\|\s*(P[012])\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|$', line)
    if match:
        rows.append({'step': int(match.group(1)), 'priority': match.group(2), 'implementation': match.group(3), 'dependency': match.group(4), 'criterion': match.group(5)})
errors = []
expected = list(range(501, 701))
if [row['step'] for row in rows] != expected:
    errors.append('numeração não é contínua de 501 a 700')
if len(rows) != 200:
    errors.append(f'quantidade encontrada: {len(rows)}')
for row in rows:
    if not row['implementation'] or not row['dependency'] or not row['criterion']:
        errors.append(f'campos incompletos no passo {row["step"]}')
result = {'file': str(path), 'count': len(rows), 'first': rows[0]['step'] if rows else None, 'last': rows[-1]['step'] if rows else None, 'priorities': {key: sum(row['priority'] == key for row in rows) for key in ('P0', 'P1', 'P2')}, 'errors': errors, 'status': 'VALID' if not errors else 'GAP'}
out = path.with_name('validacao_novas_200_implementacoes.json')
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
if errors:
    raise SystemExit(1)
