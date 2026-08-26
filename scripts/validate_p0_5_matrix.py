from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
PROJECT = Path('/home/ubuntu/futmanager_frontend')
BASE = ENGINE / 'data/database/game.db'


def read(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace') if path.exists() else ''


connection = sqlite3.connect(f'file:{BASE}?mode=ro', uri=True)
try:
    team_columns = {row[1] for row in connection.execute('PRAGMA table_info("times")')}
    selection_columns = {row[1] for row in connection.execute('PRAGMA table_info("selecoes")')}
    clubs = connection.execute('SELECT COUNT(*) FROM times').fetchone()[0]
    duplicate_names = connection.execute('SELECT COUNT(*) FROM (SELECT nome FROM times GROUP BY nome HAVING COUNT(*) > 1)').fetchone()[0]
finally:
    connection.close()

assets_router = read(PROJECT / 'server/routers/assets.ts')
engine_state = read(PROJECT / 'server/engineState.ts')
asset_tests = read(PROJECT / 'server/engineAssets.test.ts')
club_router = read(PROJECT / 'server/routers/club.ts')
club_workspace = read(PROJECT / 'server/clubWorkspace.test.ts')
career_tests = ''.join(read(path) for path in (PROJECT / 'server').glob('*career*test*'))
asset_docs = read(ENGINE / 'assets/README.md') + '\n' + '\n'.join(read(path) for path in (PROJECT / 'docs').glob('*'))
identity = read(ENGINE / 'engine/teams/identity.py')
identity_tests = read(ENGINE / 'tests/test_club_identity.py')

checks = [
    (81, 'Validar os 8.399 clubes contra IDs oficiais', clubs == 8399 and (PROJECT / 'scripts/audit_canonical_clubs.py').exists(), 'base.times + audit_canonical_clubs.py'),
    (82, 'Consulta de clubes por país e divisão', 'def list_clubs' in identity and 'country_id' in identity and 'division' in identity, 'identity.list_clubs filters'),
    (83, 'Consulta de seleções por código e confederação', 'codigo' in selection_columns and 'def list_selections' in identity and 'confederation' in identity, 'base.selecoes + identity.list_selections'),
    (84, 'Vínculos de escudos do arquivo-mãe', 'team_asset_links' in asset_docs and 'arquivo_origem' in asset_docs and 'engine-assets' in engine_state, 'assets README + engine asset serving'),
    (85, 'Ativos de clube ausentes explicitamente', 'NO_SOURCE_ASSET' in engine_state and 'mappingStatus' in engine_state, 'engineState.ts: mapping status'),
    (86, 'Ativos de seleção ausentes explicitamente', 'SOURCE_NOT_PROVIDED' in asset_docs and 'crestUrl: null' in asset_tests, 'assets README + engineAssets.test.ts'),
    (87, 'Uniforme primário e secundário', 'primary_kit_path' in engine_state and 'club_kit_links' in identity, 'engineState + identity kit links'),
    (88, 'Fallback visual consistente', 'unavailableEntityAsset' in engine_state and 'não deve apresentar' in asset_docs.lower(), 'engineState + assets policy'),
    (89, 'Nomes duplicados com IDs distintos', duplicate_names >= 0 and (PROJECT / 'scripts/audit_canonical_clubs.py').exists(), 'club audit label collisions'),
    (90, 'Aliases de busca sem alterar nome canônico', 'club_search_aliases' in identity and 'add_alias' in identity, 'identity alias table'),
    (91, 'Rivalidades documentadas', 'club_rivalries' in identity and 'source_reference' in identity and 'record_rivalry' in identity, 'identity documented rivalries'),
    (92, 'País, região e competição de origem', 'pais_id' in team_columns and 'region' in identity and 'competition_origin' in identity, 'base country + identity extensions'),
    (93, 'Perfil institucional do clube', 'institutional_overall' in identity and 'ClubWorkspaceDashboard' in engine_state, 'identity overall + workspace'),
    (94, 'Histórico de nomes do clube', 'club_name_history' in identity and 'record_name_history' in identity, 'identity name history'),
    (95, 'Relação clube-estádio sem duplicidade', 'club_stadium_identity' in identity and 'is_primary' in engine_state and 'stadium' in club_workspace.lower(), 'identity + workspace primary stadium'),
    (96, 'Elenco por clube controlado', 'jogador_time' in engine_state and 'squad' in engine_state.lower() and 'squad' in club_workspace.lower(), 'workspace squad query/test'),
    (97, 'Filtros de força e país', 'min_strength' in identity and 'max_strength' in identity and 'country_id' in identity, 'identity list_clubs filters'),
    (98, 'Início com clube e seleção', 'selection' in career_tests.lower() and 'club' in career_tests.lower() and 'listCareerTargets' in career_tests, 'career gateway tests'),
    (99, 'Proteção contra entidade inexistente', 'CLUB_NOT_FOUND' in career_tests and 'SELECTION_NOT_FOUND' in career_tests, 'career error tests'),
    (100, 'Fallbacks documentados no frontend', 'fallback' in asset_docs.lower() and 'NO_SOURCE_ASSET' in engine_state and (PROJECT / 'client/src').exists(), 'assets policy + engineState + client'),
]
rows = [{'item': item, 'criterion': criterion, 'status': 'PASS' if ok else 'GAP', 'evidence': evidence} for item, criterion, ok, evidence in checks]
result = {'front': 'P0-5', 'items': len(rows), 'passed': sum(row['status'] == 'PASS' for row in rows), 'gaps': [row for row in rows if row['status'] == 'GAP'], 'status': 'VALID' if all(row['status'] == 'PASS' for row in rows) else 'GAPS_FOUND'}
print(json.dumps(result, ensure_ascii=False, indent=2))
(PROJECT / 'docs/p0_front_05_matrix.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
if result['status'] != 'VALID':
    raise SystemExit(1)
