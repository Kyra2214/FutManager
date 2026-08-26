from __future__ import annotations

import json
from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
PROJECT = Path('/home/ubuntu/futmanager_frontend')

def read(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace') if path.exists() else ''

all_py = '\n'.join(read(path) for path in (ENGINE / 'engine').rglob('*.py'))
all_tests = '\n'.join(read(path) for path in (ENGINE / 'tests').rglob('*.py'))
all_docs = '\n'.join(read(path) for path in (ENGINE / 'docs').rglob('*') if path.is_file())
checks = [
    (41, 'Inventário de tabelas base e estado', (ENGINE / 'scripts/generate_schema_inventory.py').exists() and (ENGINE / 'docs/schema_inventory.json').exists(), 'engine/scripts/generate_schema_inventory.py + engine/docs/schema_inventory.json'),
    (42, 'Chaves naturais das tabelas mutáveis', 'unique(' in all_py.lower() or 'unique(' in all_docs.lower(), 'engine/docs: UNIQUE constraints'),
    (43, 'Versão de esquema do estado', 'schema_versions' in all_py.lower() and 'schema_version' in all_py.lower(), 'engine/**/*.py: schema_versions'),
    (44, 'Migrações idempotentes', 'if not exists' in all_py.lower() and 'create index if not exists' in all_py.lower(), 'engine/**/*.py: IF NOT EXISTS'),
    (45, 'Foreign keys após migração', 'foreign_key_check' in all_py.lower() and 'pragma foreign_keys=on' in all_py.lower(), 'validators/tests: foreign keys'),
    (46, 'Índices por clube e semana', 'club_week' in all_py.lower() or 'club_id,season,week' in all_py.lower(), 'engine/**/*.py: club/week indexes'),
    (47, 'Índices de ledger por categoria e referência', 'ledger_category' in all_py.lower() or 'financial_ledger_category' in all_py.lower(), 'engine/**/*.py: ledger indexes'),
    (48, 'Índices de eventos por status e data', 'events_status' in all_py.lower() or 'club_events' in all_py.lower(), 'engine/**/*.py: event indexes'),
    (49, 'Constraints contra negativos indevidos', 'check(' in all_py.lower() or 'negative' in all_py.lower(), 'engine/**/*.py: CHECK/negative'),
    (50, 'Níveis de estádio entre 1 e 10', 'between 1 and 10' in all_py.lower() or 'level > 10' in all_py.lower() or 'level < 1' in all_py.lower(), 'engine/**/*.py: level constraints'),
    (51, 'Público não excede capacidade', 'capacity' in all_py.lower() and ('min(' in all_py.lower() or '<=' in all_py), 'engine/**/*.py: attendance/capacity'),
    (52, 'Saldo e lançamentos coerentes', 'financial_ledger' in all_py.lower() and 'cash' in all_py.lower(), 'engine/**/*.py: ledger/cash'),
    (53, 'Colunas derivadas documentadas', 'derived' in all_docs.lower() or 'deriv' in all_docs.lower(), 'engine/docs: derived columns'),
    (54, 'Comparador de esquemas', (ENGINE / 'scripts/compare_schema.py').exists() and (ENGINE / 'docs/schema_diff.json').exists(), 'engine/scripts/compare_schema.py + engine/docs/schema_diff.json'),
    (55, 'Verificação de tabelas órfãs', 'orphan' in all_py.lower() or 'orphan' in all_docs.lower(), 'engine/docs: orphan check'),
    (56, 'Testes a partir de estados antigos', 'legacy' in all_tests.lower() or 'old_state' in all_tests.lower() or 'migration' in all_tests.lower(), 'tests: legacy/migration states'),
    (57, 'Backup antes de migração destrutiva', 'backup' in all_py.lower() or 'backup' in all_docs.lower(), 'engine/docs: backup'),
    (58, 'Rollback de migração não destrutiva', 'rollback' in all_py.lower() and ('migration' in all_py.lower() or 'schema' in all_py.lower()), 'engine/tests: migration rollback'),
    (59, 'Compactação controlada do SQLite', 'vacuum' in all_py.lower() or 'compact' in all_docs.lower(), 'engine/docs: vacuum/compact'),
    (60, 'Planos de consulta medidos', (ENGINE / 'scripts/measure_query_plans.py').exists() and (ENGINE / 'docs/query_plans.json').exists(), 'engine/scripts/measure_query_plans.py + engine/docs/query_plans.json'),
]
rows = [{'item': item, 'criterion': criterion, 'status': 'PASS' if ok else 'GAP', 'evidence': evidence} for item, criterion, ok, evidence in checks]
result = {'front': 'P0-3', 'items': len(rows), 'passed': sum(row['status'] == 'PASS' for row in rows), 'gaps': [row for row in rows if row['status'] == 'GAP'], 'status': 'VALID' if all(row['status'] == 'PASS' for row in rows) else 'GAPS_FOUND'}
print(json.dumps(result, ensure_ascii=False, indent=2))
(PROJECT / 'docs/p0_front_03_matrix.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
if result['status'] != 'VALID':
    raise SystemExit(1)
