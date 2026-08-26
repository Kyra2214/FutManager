from __future__ import annotations

from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
FRONT = Path('/home/ubuntu/futmanager_frontend')

checks = {
    'domain_error_catalog': ENGINE / 'engine/core/domain_errors.py',
    'execution_context': ENGINE / 'engine/core/execution.py',
    'roadmap_gate': ENGINE / 'engine/core/roadmap_gate.py',
    'state_path_guard': ENGINE / 'engine/core/state_store.py',
    'weekly_orchestrator': ENGINE / 'engine/world/orchestrator.py',
    'simulation_batch': ENGINE / 'engine/world/simulation.py',
    'gateway_contract': ENGINE / 'scripts/career_gateway.py',
    'architecture_contract_tests': ENGINE / 'tests/test_execution_contracts.py',
    'gateway_tests': ENGINE / 'tests/test_career_gateway.py',
    'policy_document': FRONT / 'docs/roadmap_execution_policy.md',
}

required_tokens = {
    'domain_error_catalog': ('class DomainErrorCode', 'def error_code'),
    'execution_context': ('class ExecutionContext', 'seed', 'scope'),
    'roadmap_gate': ('class RoadmapGate', 'assert_front_allowed'),
    'state_path_guard': ('assert_mutable_state_path', 'game.db'),
    'weekly_orchestrator': ('managed_transaction', 'orchestration_audit'),
    'simulation_batch': ('simulation_audit', 'ALREADY_PROCESSED'),
    'gateway_contract': ('def run', 'choices=[', 'service'),
    'architecture_contract_tests': ('ExecutionContext', 'DomainErrorCode'),
    'gateway_tests': ('career_gateway', 'subprocess.run'),
    'policy_document': ('SQL/GameState', 'P1 e P2'),
}

missing_files = [name for name, path in checks.items() if not path.exists()]
missing_tokens: dict[str, list[str]] = {}
for name, path in checks.items():
    if not path.exists():
        continue
    text = path.read_text(encoding='utf-8', errors='replace')
    absent = [token for token in required_tokens[name] if token not in text]
    if absent:
        missing_tokens[name] = absent

result = {
    'front': 'P0-2',
    'files_checked': len(checks),
    'missing_files': missing_files,
    'missing_tokens': missing_tokens,
    'status': 'VALID' if not missing_files and not missing_tokens else 'GAPS_FOUND',
}
print(result)
if result['status'] != 'VALID':
    raise SystemExit(1)
