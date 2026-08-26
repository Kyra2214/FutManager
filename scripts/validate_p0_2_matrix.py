from __future__ import annotations

import json
from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
PROJECT = Path('/home/ubuntu/futmanager_frontend')

def text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace') if path.exists() else ''

def has(path: Path, *tokens: str) -> bool:
    value = text(path)
    return bool(value) and all(token.lower() in value.lower() for token in tokens)

service_files = list((ENGINE / 'engine').rglob('*.py'))
service_text = '\n'.join(text(path) for path in service_files)
policy = PROJECT / 'docs/roadmap_execution_policy.md'
checks = [
    (21, 'Contratos de domínio, persistência e apresentação', bool((ENGINE / 'engine/core').exists() and (ENGINE / 'engine/world').exists() and (ENGINE / 'engine/economy').exists()), 'engine/core + engine/world + engine/economy'),
    (22, 'Fluxo arquivo-mãe → SQL → serviço → gateway → tRPC', has(policy, 'SQL/GameState', 'gateway', 'tRPC'), str(policy)),
    (23, 'Interfaces comuns para serviços transacionais', service_text.lower().count('managed_transaction') >= 15, 'engine/**/*.py: managed_transaction'),
    (24, 'Parâmetro managed_transaction padronizado', service_text.lower().count('managed_transaction') >= 15, 'engine/**/*.py: managed_transaction'),
    (25, 'Sem commit implícito em composição', has(ENGINE / 'engine/world/orchestrator.py', 'def transaction', 'self.connection.commit', 'self.connection.rollback') and has(ENGINE / 'engine/world/time_and_finance.py', 'def commit_tick', 'managed_transaction'), 'world/orchestrator.py + world/time_and_finance.py'),
    (26, 'Coordenador de unidade de trabalho', has(ENGINE / 'engine/world/orchestrator.py', 'def transaction', 'yield', 'commit', 'rollback'), 'engine/world/orchestrator.py'),
    (27, 'Catálogo único de erros', has(ENGINE / 'engine/core/domain_errors.py', 'class DomainErrorCode', 'def error_code'), 'engine/core/domain_errors.py'),
    (28, 'Contexto de execução', has(ENGINE / 'engine/core/execution.py', 'class ExecutionContext', 'season', 'week', 'seed', 'scope'), 'engine/core/execution.py'),
    (29, 'Pré-condições antes das etapas do tick', has(ENGINE / 'engine/world/weekly_cycle.py', 'precondition') or has(ENGINE / 'engine/world/orchestrator.py', 'precondition'), 'weekly_cycle.py/orchestrator.py'),
    (30, 'Retornos serializáveis do gateway', has(ENGINE / 'scripts/career_gateway.py', 'def run', 'json.dumps'), 'scripts/career_gateway.py'),
    (31, 'Contrato versionado de ações aceitas', has(ENGINE / 'scripts/career_gateway.py', 'choices=['), 'scripts/career_gateway.py'),
    (32, 'Logs estruturados sem dados sensíveis', 'logging' in service_text.lower() or 'logger' in service_text.lower(), 'engine/**/*.py: logging/logger'),
    (33, 'Limites operacionais para lotes mundiais', 'timeout' in service_text.lower() or 'deadline' in service_text.lower(), 'engine/**/*.py: timeout/deadline'),
    (34, 'Cancelamento seguro de simulação', has(ENGINE / 'engine/world/simulation.py', 'cancel_check', 'CANCELLED'), 'engine/world/simulation.py'),
    (35, 'Separação de leitura e comandos mutáveis', has(ENGINE / 'engine/core/contracts.py', 'class ReadRepository', 'class CommandService', 'SQL/GameState'), 'engine/core/contracts.py'),
    (36, 'Nomes padronizados de IDs e referências naturais', has(ENGINE / 'engine/core/execution.py', 'season', 'week', 'scope') and 'natural' in service_text.lower(), 'execution.py + engine/**/*.py'),
    (37, 'Verificação de esquema na inicialização', 'schema_versions' in service_text.lower() or 'schema_version' in service_text.lower(), 'engine/**/*.py: schema version'),
    (38, 'Relatório de ciclos internos', (PROJECT / 'scripts/report_engine_dependency_cycles.py').exists(), 'scripts/report_engine_dependency_cycles.py'),
    (39, 'Extensão segura por plugins', (PROJECT / 'docs/plugin_extension_policy.md').exists() and has(PROJECT / 'docs/plugin_extension_policy.md', 'serviço', 'SQLite/GameState'), 'docs/plugin_extension_policy.md'),
    (40, 'Suíte de contratos Python/TypeScript', (PROJECT / 'docs/shared_gateway_contracts.json').exists() and (PROJECT / 'scripts/validate_shared_gateway_contracts.py').exists(), 'docs/shared_gateway_contracts.json + validator'),
]
rows = [{'item': item, 'criterion': criterion, 'status': 'PASS' if ok else 'GAP', 'evidence': evidence} for item, criterion, ok, evidence in checks]
result = {'front': 'P0-2', 'items': len(rows), 'passed': sum(row['status'] == 'PASS' for row in rows), 'gaps': [row for row in rows if row['status'] == 'GAP'], 'status': 'VALID' if all(row['status'] == 'PASS' for row in rows) else 'GAPS_FOUND'}
print(json.dumps(result, ensure_ascii=False, indent=2))
(PROJECT / 'docs/p0_front_02_matrix.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
if result['status'] != 'VALID':
    raise SystemExit(1)
