from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def schema(path: Path) -> dict[str, dict]:
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        result = {}
        for (name,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
            result[name] = {
                'columns': [row[1] for row in connection.execute(f"PRAGMA table_info(\"{name}\")")],
                'indexes': [row[1] for row in connection.execute(f"PRAGMA index_list(\"{name}\")")],
            }
        return result
    finally:
        connection.close()


def compare(base: dict[str, dict], state: dict[str, dict]) -> dict:
    base_tables = set(base)
    state_tables = set(state)
    missing_tables = sorted(base_tables - state_tables)
    added_tables = sorted(state_tables - base_tables)
    tables = {}
    for table in sorted(base_tables & state_tables):
        base_columns = set(base[table]['columns'])
        state_columns = set(state[table]['columns'])
        base_indexes = set(base[table]['indexes'])
        state_indexes = set(state[table]['indexes'])
        if base_columns - state_columns or base_indexes - state_indexes:
            tables[table] = {
                'missing_columns_in_state': sorted(base_columns - state_columns),
                'added_columns_in_state': sorted(state_columns - base_columns),
                'missing_indexes_in_state': sorted(base_indexes - state_indexes),
                'added_indexes_in_state': sorted(state_indexes - base_indexes),
            }
    return {'missing_tables_in_state': missing_tables, 'added_tables_in_state': added_tables, 'table_differences': tables}


def main() -> None:
    parser = argparse.ArgumentParser(description='Compara esquemas sem escrever nos bancos.')
    parser.add_argument('--base', type=Path, default=ROOT / 'data/database/game.db')
    parser.add_argument('--state', type=Path, default=ROOT / 'data/state/game.db')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/schema_diff.json')
    args = parser.parse_args()
    result = compare(schema(args.base), schema(args.state))
    result['policy'] = 'Estado pode adicionar tabelas/colunas/índices; tabelas e colunas canônicas ausentes são divergências inesperadas.'
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(args.output), 'missing_tables': len(result['missing_tables_in_state']), 'added_tables': len(result['added_tables_in_state']), 'table_differences': len(result['table_differences'])}, ensure_ascii=False))
    if result['missing_tables_in_state'] or any(item['missing_columns_in_state'] for item in result['table_differences'].values()):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
