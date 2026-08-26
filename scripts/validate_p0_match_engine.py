from __future__ import annotations

from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
implementation = (ENGINE / 'engine/competitions/match_engine.py').read_text(encoding='utf-8', errors='replace')
tests = '\n'.join(path.read_text(encoding='utf-8', errors='replace') for path in (ENGINE / 'tests').glob('test_*.py'))

implementation_tokens = ('class CompetitionService', 'def play', 'seed', "'PLAYED'", 'commit')
test_tokens = ('MATCH_NOT_FOUND', 'MATCH_NOT_PLAYED', 'seed=', 'rollback', 'idempot')
missing_implementation = [token for token in implementation_tokens if token not in implementation]
missing_tests = [token for token in test_tokens if token not in tests]
result = {
    'front': 'P0-11',
    'implementation': str(ENGINE / 'engine/competitions/match_engine.py'),
    'missing_implementation_tokens': missing_implementation,
    'missing_test_tokens': missing_tests,
    'status': 'VALID' if not missing_implementation and not missing_tests else 'GAPS_FOUND',
}
print(result)
if result['status'] != 'VALID':
    raise SystemExit(1)
