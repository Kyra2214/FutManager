from pathlib import Path
import re

path = Path('/home/ubuntu/futmanager_frontend/roadmap_500_proximos_passos.md')
lines = path.read_text(encoding='utf-8').splitlines()
items = [re.sub(r'^\d+\. ', '', line) for line in lines if re.match(r'^\d+\. ', line)]
result = {
    'count': len(items),
    'first': items[0] if items else None,
    'last': items[-1] if items else None,
    'duplicate_items': len(items) - len(set(items)),
}
print(result)
assert result['count'] == 500
assert result['duplicate_items'] == 0
assert lines[0].startswith('# FutManager/Brasfoot')
