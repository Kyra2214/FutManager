from pathlib import Path

ROOT = Path('/home/ubuntu/brasfoot_engine/engine')
TARGETS = [
    ROOT / 'ai/club_ai.py',
    ROOT / 'commercial/sponsorship_media.py',
    ROOT / 'competitions/match_engine.py',
    ROOT / 'competitions/structure.py',
    ROOT / 'core/global_integration.py',
    ROOT / 'economy/institutional_power.py',
    ROOT / 'economy/matchday_revenue.py',
    ROOT / 'economy/sponsorships.py',
    ROOT / 'economy/staff_market.py',
    ROOT / 'economy/world_economy.py',
    ROOT / 'events/service.py',
    ROOT / 'scouting/service.py',
    ROOT / 'social/attendance.py',
    ROOT / 'social/stadium_fans.py',
    ROOT / 'sports/cycle.py',
    ROOT / 'staff/state_store.py',
    ROOT / 'transfers/market.py',
    ROOT / 'world/orchestrator.py',
    ROOT / 'world/simulation.py',
    ROOT / 'world/weekly_cycle.py',
    ROOT / 'rules/state_store.py',
]

replacements = {
    'self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db': 'assert_mutable_state_path(db) if not isinstance(db,sqlite3.Connection) else None;self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db',
    'self.connection = sqlite3.connect(str(db)) if not isinstance(db, sqlite3.Connection) else db': 'assert_mutable_state_path(db) if not isinstance(db, sqlite3.Connection) else None\n        self.connection = sqlite3.connect(str(db)) if not isinstance(db, sqlite3.Connection) else db',
    'self.connection=sqlite3.connect(database) if not isinstance(database,sqlite3.Connection) else database': 'assert_mutable_state_path(database) if not isinstance(database,sqlite3.Connection) else None;self.connection=sqlite3.connect(database) if not isinstance(database,sqlite3.Connection) else database',
    'self.connection = sqlite3.connect(str(database)) if not isinstance(database, sqlite3.Connection) else database': 'assert_mutable_state_path(database) if not isinstance(database, sqlite3.Connection) else None\n        self.connection = sqlite3.connect(str(database)) if not isinstance(database, sqlite3.Connection) else database',
    'self.connection=sqlite3.connect(state_db)': 'assert_mutable_state_path(state_db);self.connection=sqlite3.connect(state_db)',
    'self.connection = sqlite3.connect(state_db)': 'assert_mutable_state_path(state_db)\n        self.connection = sqlite3.connect(state_db)',
}

for path in TARGETS:
    text = path.read_text(encoding='utf-8')
    changed = False
    for old, new in replacements.items():
        if old in text and 'assert_mutable_state_path' not in text:
            text = text.replace(old, new, 1)
            changed = True
    if changed:
        lines = text.splitlines()
        insert_at = 0
        while insert_at < len(lines) and (lines[insert_at].startswith('from ') or lines[insert_at].startswith('import ') or not lines[insert_at].strip()):
            insert_at += 1
        lines.insert(insert_at, 'from engine.core.state_store import assert_mutable_state_path')
        path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print('patched', path.relative_to(ROOT))
    else:
        print('unchanged', path.relative_to(ROOT))
