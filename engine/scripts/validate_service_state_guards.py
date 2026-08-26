from __future__ import annotations

import re
from pathlib import Path

ROOT = Path('/home/ubuntu/brasfoot_engine/engine')
READ_ONLY_OR_CONNECTION_ONLY = {
    ROOT / 'core/consistency.py',
    ROOT / 'world/time_and_finance.py',
    ROOT / 'database/repositories.py',
}

path_open_pattern = re.compile(r'sqlite3\.connect\((?:str\()?\s*(db|database|state_db|self\.path)')
violations = []
checked = []
for path in ROOT.rglob('*.py'):
    text = path.read_text(encoding='utf-8')
    if not path_open_pattern.search(text):
        continue
    if path in READ_ONLY_OR_CONNECTION_ONLY:
        continue
    checked.append(str(path.relative_to(ROOT)))
    if 'assert_mutable_state_path' not in text:
        violations.append(str(path.relative_to(ROOT)))

assert not violations, f'unguarded path-open services: {violations}'
print('service-state-guards=ok')
print({'path_open_services_checked': len(checked), 'unguarded': len(violations)})
