from __future__ import annotations

from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
implementation = (ENGINE / 'engine/economy/sponsorships.py').read_text(encoding='utf-8', errors='replace')
tests = (ENGINE / 'tests/test_sponsorships.py').read_text(encoding='utf-8', errors='replace')
power = (ENGINE / 'engine/economy/institutional_power.py').read_text(encoding='utf-8', errors='replace')
required_impl = ('star_rating', 'overall', 'offer_set', 'sponsor_missions', 'SPONSOR_MISSION', 'event_progress')
required_tests = ('seed=', 'idempot', 'mission', 'offer', 'star')
missing = {
    'implementation': [token for token in required_impl if token.lower() not in implementation.lower()],
    'tests': [token for token in required_tests if token.lower() not in tests.lower()],
    'institutional_power': [token for token in ('overall', 'squad_score', 'stadium_score', 'ct_score') if token.lower() not in power.lower()],
}
result = {'front': 'P0-15', 'missing': missing, 'status': 'VALID' if not any(missing.values()) else 'GAPS_FOUND'}
print(result)
if result['status'] != 'VALID':
    raise SystemExit(1)
