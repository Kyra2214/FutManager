from __future__ import annotations

from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
implementation = (ENGINE / 'engine/world/simulation.py').read_text(encoding='utf-8', errors='replace')
tests = (ENGINE / 'tests/test_phases16_17.py').read_text(encoding='utf-8', errors='replace')
required_impl = ('class SimulationLevel', 'simulate_batch', 'cancel_check', 'simulation_audit', 'ALREADY_PROCESSED', 'priority_club_id')
required_tests = ('SimulationLevel.FAST', 'ALREADY_PROCESSED', 'CANCELLED', 'simulation_audit', 'seed=')
missing = {
    'implementation': [token for token in required_impl if token.lower() not in implementation.lower()],
    'tests': [token for token in required_tests if token.lower() not in tests.lower()],
}
result = {'front': 'P0-16', 'missing': missing, 'status': 'VALID' if not any(missing.values()) else 'GAPS_FOUND'}
print(result)
if result['status'] != 'VALID':
    raise SystemExit(1)
