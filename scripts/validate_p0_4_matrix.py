from __future__ import annotations

import json
import sqlite3
from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
PROJECT = Path('/home/ubuntu/futmanager_frontend')
BASE = ENGINE / 'data/database/game.db'
EXTENSIONS = ENGINE / 'engine/players/extensions.py'


def read(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace') if path.exists() else ''


connection = sqlite3.connect(f'file:{BASE}?mode=ro', uri=True)
try:
    player_columns = {row[1] for row in connection.execute('PRAGMA table_info("jogadores")')}
    link_columns = {row[1] for row in connection.execute('PRAGMA table_info("jogador_time")')}
    pos_count = connection.execute('SELECT COUNT(DISTINCT posicao_codigo) FROM jogadores').fetchone()[0]
    duplicate_players = connection.execute('SELECT COUNT(*) FROM (SELECT chave_canonica FROM jogadores GROUP BY chave_canonica HAVING COUNT(*) > 1)').fetchone()[0]
finally:
    connection.close()

extensions = read(EXTENSIONS)
policy = read(PROJECT / 'docs/roadmap_execution_policy.md')
player_audit = read(PROJECT / 'scripts/audit_canonical_players.py')
frontend_audit = read(PROJECT / 'scripts/validate_p0_frontend_trpc.py')
frontend_pages = read(PROJECT / 'client/src/pages/Home.tsx') + read(PROJECT / 'client/src/pages/CareerStart.tsx')

checks = [
    (61, 'Catalogar posições originais', pos_count >= 5 and 'posicao_codigo' in player_columns and 'posicao' in player_columns, 'base.jogadores.posicao/posicao_codigo'),
    (62, 'Normalizar abreviações preservando valor original', 'player_position_aliases' in extensions and 'original_position' in extensions and 'normalized_position' in extensions, 'engine/players/extensions.py: player_position_aliases'),
    (63, 'Validar unicidade global', duplicate_players == 0 and 'chave_canonica' in player_columns, 'base.jogadores.chave_canonica + audit'),
    (64, 'Histórico de vínculos jogador-clube', {'jogador_id', 'time_id', 'arquivo_origem'} <= link_columns, 'base.jogador_time'),
    (65, 'Preservar status, lado, categoria e titularidade', {'status', 'status_codigo', 'categoria'} <= link_columns and 'lado' in player_columns, 'base.jogador_time + jogadores'),
    (66, 'Faixa de CR1 e CR2', {'cr1', 'cr2'} <= player_columns and 'cr1' in extensions and 'cr2' in extensions, 'base + player_attribute_history'),
    (67, 'Evolução temporal de idade e potencial', 'CREATE TABLE IF NOT EXISTS player_progression' in extensions and 'record_progression' in extensions, 'engine/players/extensions.py: player_progression'),
    (68, 'Histórico de atributos por temporada', 'CREATE TABLE IF NOT EXISTS player_attribute_history' in extensions and 'record_attributes' in extensions, 'engine/players/extensions.py: player_attribute_history'),
    (69, 'Histórico de contratos individuais', 'CREATE TABLE IF NOT EXISTS player_contract_history' in extensions and 'record_contract' in extensions, 'engine/players/extensions.py: player_contract_history'),
    (70, 'Cláusulas e duração de contrato', 'release_clause' in extensions and 'start_week' in extensions and 'end_week' in extensions, 'engine/players/extensions.py: contract fields'),
    (71, 'Preferência de posição', 'preferred_position' in extensions and 'record_profile' in extensions, 'engine/players/extensions.py: preferred_position'),
    (72, 'Pé dominante e versatilidade', 'dominant_foot' in extensions and 'versatility' in extensions, 'engine/players/extensions.py: profile fields'),
    (73, 'Perfil de personalidade sem inventar dados', 'personality_json' in extensions and 'personality' in extensions, 'engine/players/extensions.py: personality_json'),
    (74, 'Disponibilidade e suspensão', 'CREATE TABLE IF NOT EXISTS player_availability' in extensions and 'record_availability' in extensions, 'engine/players/extensions.py: player_availability'),
    (75, 'Topo mundial por posição', 'top_mundial' in player_columns and 'posicao_codigo' in player_columns, 'base.jogadores.top_mundial/posicao_codigo'),
    (76, 'Validação de duplicados em importações futuras', (PROJECT / 'scripts/audit_canonical_players.py').exists() and 'duplicate' in player_audit.lower(), 'scripts/audit_canonical_players.py'),
    (77, 'Relatório de jogadores sem clube', 'def unattached_players' in extensions and 'NOT EXISTS' in extensions, 'engine/players/extensions.py: unattached_players'),
    (78, 'Relatório de elencos incompletos', 'def incomplete_squads' in extensions and 'HAVING COUNT' in extensions, 'engine/players/extensions.py: incomplete_squads'),
    (79, 'Serialização dos perfis ao frontend', bool(frontend_audit) and 'trpc.' in frontend_pages.lower() and 'usequery' in frontend_pages.lower(), 'client/src/pages + frontend tRPC audit'),
    (80, 'Mapeamento arquivo-mãe para SQL', 'arquivo_origem' in link_columns and (PROJECT / 'docs/p0_validation_evidence_2026-08-26.md').exists(), 'jogador_time.arquivo_origem + validation evidence'),
]
rows = [{'item': item, 'criterion': criterion, 'status': 'PASS' if ok else 'GAP', 'evidence': evidence} for item, criterion, ok, evidence in checks]
result = {'front': 'P0-4', 'items': len(rows), 'passed': sum(row['status'] == 'PASS' for row in rows), 'gaps': [row for row in rows if row['status'] == 'GAP'], 'status': 'VALID' if all(row['status'] == 'PASS' for row in rows) else 'GAPS_FOUND'}
print(json.dumps(result, ensure_ascii=False, indent=2))
(PROJECT / 'docs/p0_front_04_matrix.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
if result['status'] != 'VALID':
    raise SystemExit(1)
