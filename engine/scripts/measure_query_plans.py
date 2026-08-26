from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATABASES = {'base': ROOT / 'data/database/game.db', 'state': ROOT / 'data/state/game.db'}
QUERIES = {
    'players_by_position': 'SELECT jogador_id, posicao FROM jogadores ORDER BY jogador_id LIMIT 25',
    'players_by_club': 'SELECT jogador_id, clube_id FROM jogadores_clubes ORDER BY clube_id, jogador_id LIMIT 25',
    'ledger_by_club_week': 'SELECT * FROM financial_ledger WHERE club_id=? AND season=? AND week=?',
    'events_by_status_date': 'SELECT * FROM club_events WHERE status=? ORDER BY created_at DESC LIMIT 25',
}

def tables(connection: sqlite3.Connection) -> set[str]:
    return {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}

def measure(path: Path) -> dict:
    connection = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
    try:
        available = tables(connection)
        plans = {}
        for name, query in QUERIES.items():
            try:
                plan = [list(row) for row in connection.execute('EXPLAIN QUERY PLAN ' + query, (0, 1, 1) if 'club_id=?' in query else ("OPEN",))]
                plans[name] = {'status': 'MEASURED', 'plan': plan}
            except sqlite3.Error as error:
                plans[name] = {'status': 'SKIPPED', 'reason': str(error)}
        return {'path': str(path), 'tables': sorted(available), 'plans': plans}
    finally:
        connection.close()

result = {'databases': {name: measure(path) for name, path in DATABASES.items()}}
output = ROOT / 'docs/query_plans.json'
output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
measured = sum(item['status'] == 'MEASURED' for database in result['databases'].values() for item in database['plans'].values())
print({'output': str(output), 'measured_plans': measured, 'status': 'VALID' if measured > 0 else 'GAPS_FOUND'})
if measured == 0:
    raise SystemExit(1)
