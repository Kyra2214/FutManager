from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def audit(path: Path) -> dict:
    connection = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        result = {'path': str(path), 'integrity_check': connection.execute('PRAGMA integrity_check').fetchone()[0], 'foreign_key_check_count': len(connection.execute('PRAGMA foreign_key_check').fetchall())}
        result['players'] = {
            'count': connection.execute('SELECT COUNT(*) FROM jogadores').fetchone()[0],
            'duplicate_canonical_keys': [dict(row) for row in connection.execute('SELECT chave_canonica, COUNT(*) AS count FROM jogadores GROUP BY chave_canonica HAVING COUNT(*) > 1 ORDER BY count DESC, chave_canonica')],
            'null_canonical_keys': connection.execute("SELECT COUNT(*) FROM jogadores WHERE chave_canonica IS NULL OR trim(chave_canonica) = ''").fetchone()[0],
        }
        result['clubs'] = {
            'count': connection.execute('SELECT COUNT(*) FROM times').fetchone()[0],
            'duplicate_ids': [dict(row) for row in connection.execute('SELECT time_id, COUNT(*) AS count FROM times GROUP BY time_id HAVING COUNT(*) > 1')],
            'null_names': connection.execute("SELECT COUNT(*) FROM times WHERE nome IS NULL OR trim(nome) = ''").fetchone()[0],
        }
        result['selections'] = {
            'count': connection.execute('SELECT COUNT(*) FROM selecoes').fetchone()[0],
            'duplicate_ids': [dict(row) for row in connection.execute('SELECT selecao_id, COUNT(*) AS count FROM selecoes GROUP BY selecao_id HAVING COUNT(*) > 1')],
            'duplicate_codes': [dict(row) for row in connection.execute('SELECT codigo, COUNT(*) AS count FROM selecoes GROUP BY codigo HAVING COUNT(*) > 1')],
            'null_codes': connection.execute("SELECT COUNT(*) FROM selecoes WHERE codigo IS NULL OR trim(codigo) = ''").fetchone()[0],
        }
        return result
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description='Audita entidades canônicas sem escrever no SQLite.')
    parser.add_argument('--base', type=Path, default=ROOT / 'data/database/game.db')
    parser.add_argument('--state', type=Path, default=ROOT / 'data/state/game.db')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/canonical_entities_audit.json')
    args = parser.parse_args()
    result = {'base': audit(args.base), 'state': audit(args.state)}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(args.output), 'base_players': result['base']['players']['count'], 'state_players': result['state']['players']['count'], 'base_player_duplicates': len(result['base']['players']['duplicate_canonical_keys']), 'state_player_duplicates': len(result['state']['players']['duplicate_canonical_keys'])}, ensure_ascii=False))
    for item in result.values():
        assert item['integrity_check'] == 'ok'
        assert item['foreign_key_check_count'] == 0
        assert not item['players']['duplicate_canonical_keys']
        assert item['players']['null_canonical_keys'] == 0
        assert not item['clubs']['duplicate_ids']
        assert not item['selections']['duplicate_ids']
        assert not item['selections']['duplicate_codes']


if __name__ == '__main__':
    main()
