from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

ROADMAP = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_melhorias_941_3940.md')
MANIFEST = Path('/home/ubuntu/futmanager_frontend/docs/roadmap_3000_execucao.json')

@dataclass
class RoadmapItem:
    item_id: int
    priority: str
    title: str
    dependency: str
    criterion: str
    status: str = 'PENDING'
    evidence: list[str] | None = None


def load_items() -> list[RoadmapItem]:
    items: list[RoadmapItem] = []
    pattern = re.compile(r'^(\d+)\. \*\*\[(P[012])\] (.+?)\*\* — Dependência: `([^`]+)`\. Critério: (.+)\.$')
    for line in ROADMAP.read_text(encoding='utf-8').splitlines():
        match = pattern.match(line)
        if match:
            items.append(RoadmapItem(int(match.group(1)), match.group(2), match.group(3), match.group(4), match.group(5), 'PENDING', []))
    return items


def gate_status(items: list[RoadmapItem]) -> dict[str, str]:
    p0 = [item for item in items if item.priority == 'P0']
    p1 = [item for item in items if item.priority == 'P1']
    return {
        'P0_GLOBAL_GATE': 'OPEN' if p0 and all(item.status == 'DONE' for item in p0) else 'CLOSED',
        'P1_GLOBAL_GATE': 'OPEN' if p1 and all(item.status == 'DONE' for item in p1) and all(item.status == 'DONE' for item in p0) else 'CLOSED',
    }


def main() -> None:
    items = load_items()
    if MANIFEST.exists():
        previous = json.loads(MANIFEST.read_text(encoding='utf-8'))
        previous_items = {item['item_id']: item for item in previous.get('items', [])}
        for item in items:
            old = previous_items.get(item.item_id)
            if old:
                item.status = old.get('status', 'PENDING')
                item.evidence = old.get('evidence', [])
    assert len(items) == 3000
    assert [item.item_id for item in items] == list(range(941, 3941))
    gates = gate_status(items)
    payload = {
        'status': 'VALID',
        'policy': 'P0_GLOBAL_GATE -> P1_GLOBAL_GATE -> P2; SQL/GameState is the source of truth',
        'gates': gates,
        'summary': {
            'total': len(items),
            'done': sum(item.status == 'DONE' for item in items),
            'pending': sum(item.status == 'PENDING' for item in items),
            'P0': sum(item.priority == 'P0' for item in items),
            'P1': sum(item.priority == 'P1' for item in items),
            'P2': sum(item.priority == 'P2' for item in items),
        },
        'items': [asdict(item) for item in items],
    }
    MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in payload.items() if key != 'items'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
