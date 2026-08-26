from __future__ import annotations

from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
files = {
    'competition_engine': ENGINE / 'engine/competitions/match_engine.py',
    'competition_structure': ENGINE / 'engine/competitions/structure.py',
    'competition_tests': ENGINE / 'tests/test_phases10_11.py',
    'calendar_tests': ENGINE / 'tests/test_phases10_11.py',
    'integration_tests': ENGINE / 'tests/test_phase18_integration.py',
}
tokens = {
    'competition_engine': ('create_competition', 'standings', 'team_competition_stats'),
    'competition_structure': ('generate_fixtures', 'calendar', 'finish_competition'),
    'competition_tests': ('generate_fixtures', 'standings', 'PENDING_FIXTURES'),
    'calendar_tests': ('calendar', 'season'),
    'integration_tests': ('idempotency', 'rollback'),
}
missing_files = [name for name, path in files.items() if not path.exists()]
missing_tokens = {}
for name, path in files.items():
    if not path.exists():
        continue
    text = path.read_text(encoding='utf-8', errors='replace')
    absent = [token for token in tokens[name] if token not in text]
    if absent:
        missing_tokens[name] = absent
result = {
    'fronts': ['P0-12', 'P0-13'],
    'files_checked': len(files),
    'missing_files': missing_files,
    'missing_tokens': missing_tokens,
    'status': 'VALID' if not missing_files and not missing_tokens else 'GAPS_FOUND',
}
print(result)
if result['status'] != 'VALID':
    raise SystemExit(1)
