from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
BASE = ENGINE / 'data/database/game.db'
STATE = ENGINE / 'data/state/game.db'
MANIFEST = ENGINE / 'data/database/game.db.sha256'

assert BASE.exists(), f'BASE_MISSING:{BASE}'
assert STATE.exists(), f'STATE_MISSING:{STATE}'
assert MANIFEST.exists(), f'HASH_MANIFEST_MISSING:{MANIFEST}'
actual_hash = hashlib.sha256(BASE.read_bytes()).hexdigest()
assert actual_hash == MANIFEST.read_text(encoding='utf-8').strip(), 'BASE_HASH_MISMATCH'


def inspect(path: Path) -> dict[str, object]:
    uri = f'file:{path}?mode=ro'
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys=ON')
    integrity = connection.execute('PRAGMA integrity_check').fetchone()[0]
    foreign_keys = connection.execute('PRAGMA foreign_key_check').fetchall()
    tables = {row['name'] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    schema_version = None
    if 'schema_versions' in tables:
        row = connection.execute("SELECT version FROM schema_versions WHERE component='game_state'").fetchone()
        schema_version = row[0] if row else None
    expected_indexes = {
        'idx_matches_club_week',
        'idx_financial_ledger_club_week',
        'idx_financial_ledger_category_source',
        'idx_club_events_club_read_date',
    }
    indexes = {row['name'] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    relevant_indexes = sorted(expected_indexes & indexes)
    connection.close()
    return {
        'path': str(path),
        'integrity_check': integrity,
        'foreign_key_errors': len(foreign_keys),
        'tables': len(tables),
        'schema_version': schema_version,
        'relevant_indexes': relevant_indexes,
    }

base_report = inspect(BASE)
state_report = inspect(STATE)
assert base_report['integrity_check'] == 'ok' and base_report['foreign_key_errors'] == 0
assert state_report['integrity_check'] == 'ok' and state_report['foreign_key_errors'] == 0
print({'base': base_report, 'state': state_report, 'base_hash': actual_hash, 'status': 'VALID'})
