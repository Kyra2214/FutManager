from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
BASE = ENGINE / 'data/database/game.db'
REPORT = ENGINE / 'docs/canonical_players_audit.json'

connection = sqlite3.connect(f'file:{BASE}?mode=ro', uri=True)
connection.row_factory = sqlite3.Row
connection.execute('PRAGMA foreign_keys=ON')

players = connection.execute('SELECT COUNT(*) AS count FROM jogadores').fetchone()['count']
unique_keys = connection.execute('SELECT COUNT(DISTINCT chave_canonica) AS count FROM jogadores').fetchone()['count']
nulls = connection.execute('SELECT COUNT(*) AS count FROM jogadores WHERE chave_canonica IS NULL OR nome_normalizado IS NULL OR posicao IS NULL OR pais_id IS NULL').fetchone()['count']
position_rows = connection.execute('SELECT posicao_codigo, posicao, COUNT(*) AS count FROM jogadores GROUP BY posicao_codigo, posicao ORDER BY posicao_codigo').fetchall()
status_rows = connection.execute('SELECT status_codigo, status, COUNT(*) AS count FROM jogador_time GROUP BY status_codigo, status ORDER BY status_codigo').fetchall()
country_rows = connection.execute('SELECT pais_id, COUNT(*) AS count FROM jogadores GROUP BY pais_id ORDER BY pais_id').fetchall()
link_duplicates = connection.execute('SELECT jogador_id, time_id, categoria, COUNT(*) AS count FROM jogador_time GROUP BY jogador_id, time_id, categoria HAVING COUNT(*) > 1').fetchall()
unknown_positions = connection.execute('SELECT COUNT(*) AS count FROM jogadores WHERE posicao_codigo IS NULL OR trim(posicao) = ""').fetchone()['count']

report = {
    'database': str(BASE),
    'players': players,
    'distinct_canonical_keys': unique_keys,
    'null_required_fields': nulls,
    'unknown_positions': unknown_positions,
    'position_distribution': [dict(row) for row in position_rows],
    'status_distribution': [dict(row) for row in status_rows],
    'country_distribution_rows': len(country_rows),
    'duplicate_player_team_category_links': len(link_duplicates),
    'source_of_truth': 'SQL/GameState',
    'status': 'VALID' if players == unique_keys and nulls == 0 and unknown_positions == 0 and not link_duplicates else 'GAPS_FOUND',
}
connection.close()
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(report)
if report['status'] != 'VALID':
    raise SystemExit(1)
