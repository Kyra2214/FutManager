from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path('/home/ubuntu/futmanager_frontend')
roadmap = (ROOT / 'roadmap_500_proximos_passos.md').read_text(encoding='utf-8')
gate = json.loads((ROOT / 'roadmap_gate.json').read_text(encoding='utf-8'))

items = re.findall(r'^\d+\. .+$', roadmap, flags=re.MULTILINE)
fronts = re.findall(r'^## \[(P0|P1|P2)\] ', roadmap, flags=re.MULTILINE)
assert len(items) == 500, len(items)
assert len(fronts) == 25, len(fronts)
assert fronts.count('P0') == len(gate['p0_fronts'])
assert gate['sql_game_state_source_of_truth'] is True
assert gate['p1_p2_blocked'] is (gate['p0_gate'] != 'OPEN')
priorities = {int(front): priority for front, priority in gate['front_priorities'].items()}
for front, dependencies in gate['front_dependencies'].items():
    if priorities[int(front)] == 'P0':
        invalid = [dependency for dependency in dependencies if priorities[int(dependency)] != 'P0']
        assert not invalid, f'P0_FRONT_DEPENDS_ON_LATER_PRIORITY:{front}:{invalid}'
assert '| 11 | P0 | 2, 3, 4 |' in roadmap
statuses = {front['status'] for front in gate['p0_fronts']}
assert statuses <= {'PENDING', 'CONSOLIDATED'}
if gate['p0_gate'] != 'OPEN':
    assert any(front['status'] != 'CONSOLIDATED' for front in gate['p0_fronts'])
    print('P0_GATE=CLOSED; consolidação incremental permitida; P1/P2 bloqueados; SQL/GameState=fonte única declarada')
else:
    assert all(front['status'] == 'CONSOLIDATED' for front in gate['p0_fronts'])
    print('P0_GATE=OPEN; todos os fronts P0 consolidados')
print({'items': len(items), 'fronts': len(fronts), 'p0': fronts.count('P0'), 'p1': fronts.count('P1'), 'p2': fronts.count('P2')})
