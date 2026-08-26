from __future__ import annotations

from pathlib import Path

ENGINE = Path('/home/ubuntu/brasfoot_engine')
checks = {
    'world_economy': (ENGINE / 'engine/economy/world_economy.py', ('weekly', 'cash', 'club')),
    'staff_economy': (ENGINE / 'engine/economy/staff_market.py', ('payroll', 'process_weekly_costs', 'ALREADY_PROCESSED')),
    'weekly_cycle': (ENGINE / 'engine/world/weekly_cycle.py', ('process_week', 'record_matchday', 'rollback', 'managed_transaction')),
    'economy_tests': (ENGINE / 'tests/test_staff_market_economy.py', ('weekly_player_payroll', 'process_weekly_costs', 'ALREADY_PROCESSED', 'rollback')),
    'cycle_tests': (ENGINE / 'tests/test_weekly_cycle.py', ('advance_week', 'ALREADY_PROCESSED', 'rollback', 'financial_ledger')),
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
    'front': 'P0-17',
    'files_checked': len(checks),
    'missing_files': missing_files,
    'missing_tokens': missing_tokens,
    'status': 'VALID' if not missing_files and not missing_tokens else 'GAPS_FOUND',
}
print(result)
if result['status'] != 'VALID':
    raise SystemExit(1)
