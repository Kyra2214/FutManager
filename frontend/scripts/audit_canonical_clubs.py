from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
BASE = ENGINE / 'data/database/game.db'
REPORT = ENGINE / 'docs/canonical_clubs_audit.json'
connection = sqlite3.connect(f'file:{BASE}?mode=ro', uri=True)
connection.row_factory = sqlite3.Row


def count(table: str) -> int:
    return connection.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]

clubs = count('times')
selections = count('selecoes')
countries = count('paises')
club_origin_duplicates = connection.execute('SELECT arquivo_origem, COUNT(*) AS count FROM times GROUP BY arquivo_origem HAVING COUNT(*) > 1').fetchall()
club_name_duplicates = connection.execute('SELECT nome, COUNT(*) AS count FROM times GROUP BY nome HAVING COUNT(*) > 1').fetchall()
selection_code_duplicates = connection.execute('SELECT codigo, COUNT(*) AS count FROM selecoes GROUP BY codigo HAVING COUNT(*) > 1').fetchall()
selection_name_duplicates = connection.execute('SELECT nome, COUNT(*) AS count FROM selecoes GROUP BY nome HAVING COUNT(*) > 1').fetchall()
club_country_orphans = connection.execute('SELECT COUNT(*) FROM times t LEFT JOIN paises p ON p.pais_id=t.pais_id WHERE p.pais_id IS NULL').fetchone()[0]
selection_country_orphans = connection.execute('SELECT COUNT(*) FROM selecoes s LEFT JOIN paises p ON p.pais_id=s.pais_id WHERE s.pais_id IS NOT NULL AND p.pais_id IS NULL').fetchone()[0]
report = {
    'database': str(BASE),
    'clubs': clubs,
    'selections': selections,
    'countries': countries,
    'duplicate_club_origins': len(club_origin_duplicates),
    'duplicate_club_names_expected_label_collisions': len(club_name_duplicates),
    'duplicate_selection_codes': len(selection_code_duplicates),
    'duplicate_selection_names': len(selection_name_duplicates),
    'club_country_orphans': club_country_orphans,
    'selection_country_orphans': selection_country_orphans,
    'source_of_truth': 'SQL/GameState',
    'status': 'VALID' if not any((club_origin_duplicates, selection_code_duplicates, selection_name_duplicates, club_country_orphans, selection_country_orphans)) else 'GAPS_FOUND',
}
connection.close()
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(report)
if report['status'] != 'VALID':
    raise SystemExit(1)
