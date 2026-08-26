from __future__ import annotations

from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
checks = {
    'attendance': (ENGINE / 'engine/social/attendance.py', ('class AttendanceService', 'seed', 'estimate')),
    'fans': (ENGINE / 'engine/social/stadium_fans.py', ('class SocialService', 'reputation', 'fan')),
    'revenue': (ENGINE / 'engine/economy/matchday_revenue.py', ('class MatchdayRevenueService', 'ledger', 'ticket')),
    'attendance_tests': (ENGINE / 'tests/test_social_attendance.py', ('seed=', 'idempotent', 'estimate')),
    'revenue_tests': (ENGINE / 'tests/test_matchday_revenue.py', ('play(', 'ledger', 'idempot')),
    'cycle_tests': (ENGINE / 'tests/test_weekly_cycle.py', ('advance_week', 'idempot', 'rollback')),
}
missing_files = []
missing_tokens: dict[str, list[str]] = {}
for name, (path, tokens) in checks.items():
    if not path.exists():
        missing_files.append(name)
        continue
    text = path.read_text(encoding='utf-8', errors='replace').lower()
    absent = [token for token in tokens if token.lower() not in text]
    if absent:
        missing_tokens[name] = absent
result = {
    'front': 'P0-14',
    'files_checked': len(checks),
    'missing_files': missing_files,
    'missing_tokens': missing_tokens,
    'status': 'VALID' if not missing_files and not missing_tokens else 'GAPS_FOUND',
}
print(result)
if result['status'] != 'VALID':
    raise SystemExit(1)
