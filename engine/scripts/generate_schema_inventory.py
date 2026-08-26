from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inventory(path: Path) -> dict:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        tables = []
        for row in connection.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            table = row['name']
            columns = [dict(column) for column in connection.execute(f"PRAGMA table_info({table})")]
            indexes = [dict(index) for index in connection.execute(f"PRAGMA index_list({table})")]
            count = connection.execute(f"SELECT COUNT(*) AS count FROM \"{table}\"").fetchone()['count']
            tables.append({'name': table, 'row_count': int(count), 'columns': columns, 'indexes': indexes})
        return {
            'path': str(path),
            'integrity_check': connection.execute('PRAGMA integrity_check').fetchone()[0],
            'foreign_key_check_count': len(connection.execute('PRAGMA foreign_key_check').fetchall()),
            'table_count': len(tables),
            'tables': tables,
        }
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description='Gera inventário read-only dos bancos FutManager/Brasfoot.')
    parser.add_argument('--base', type=Path, default=ROOT / 'data/database/game.db')
    parser.add_argument('--state', type=Path, default=ROOT / 'data/state/game.db')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/schema_inventory.json')
    args = parser.parse_args()
    result = {'base': inventory(args.base), 'state': inventory(args.state)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(args.output), 'base_tables': result['base']['table_count'], 'state_tables': result['state']['table_count'], 'base_integrity': result['base']['integrity_check'], 'state_integrity': result['state']['integrity_check']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
