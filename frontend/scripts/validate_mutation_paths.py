from __future__ import annotations

import re
from pathlib import Path

ROOT = Path('/home/ubuntu/futmanager_frontend')
CLIENT = ROOT / 'client' / 'src'
GATEWAY = ROOT / 'server' / 'careerGateway.ts'

forbidden_client = re.compile(r'\b(?:DatabaseSync|better-sqlite3|sqlite3)\b|INSERT\s+INTO|UPDATE\s+[A-Za-z_]+\s+SET|DELETE\s+FROM|writeFile(?:Sync)?\b|unlink(?:Sync)?\b', re.IGNORECASE)
violations = []
for path in CLIENT.rglob('*'):
    if path.suffix not in {'.ts', '.tsx'}:
        continue
    text = path.read_text(encoding='utf-8')
    if forbidden_client.search(text):
        violations.append(str(path.relative_to(ROOT)))
assert not violations, f'writes or SQLite references found in frontend: {violations}'

gateway_text = GATEWAY.read_text(encoding='utf-8')
assert 'career_gateway.py' in gateway_text
assert 'execFileSync' in gateway_text

engine_gateway = Path('/home/ubuntu/brasfoot_engine/scripts/career_gateway.py')
engine_text = engine_gateway.read_text(encoding='utf-8')
assert 'import sqlite3' in engine_text
assert 'service.connection' in engine_text
assert 'service.close()' in engine_text
action_contracts = {
    'catalog': 'catalog(service.connection, payload)',
    'current': 'current(service.connection)',
    'start': 'service.start_career',
    'economy_bootstrap_all': 'StaffMarketService(service.connection).bootstrap_all_clubs',
    'economy_weekly_all': 'WorldEconomyService(service.connection).process_world_week',
    'sponsor_bootstrap_all': 'SponsorshipService(service.connection).bootstrap_all_clubs',
    'sponsor_weekly_all': 'SponsorshipService(service.connection).process_week_all',
    'stadium_bootstrap_all': 'StadiumService(service.connection).bootstrap_all_clubs',
    'weekly_advance': 'WeeklyWorldCycleService(service.connection).advance_week',
    'economy_bootstrap': 'market.bootstrap_club',
    'economy_summary': 'market.summary',
    'staff_catalog': 'market.available_staff',
    'staff_hire': 'market.hire_staff',
    'department_offers': 'market.department_offer',
    'department_upgrade': 'market.upgrade_department',
    'economy_weekly': 'market.process_weekly_costs',
    'sponsor_bootstrap': 'service.bootstrap_club',
    'sponsor_summary': 'service.summary',
    'sponsor_offers': 'service.offers',
    'sponsor_accept': 'service.accept_offer',
    'sponsor_weekly': 'service.process_week',
    'stadium_bootstrap': 'stadiums.bootstrap_club',
    'stadium_summary': 'attendance_rows',
    'stadium_upgrade': 'stadiums.upgrade_stadium_component',
    'ticket_price': 'attendance.configure_ticket_price',
    'events_list': 'events.list_for_club',
    'events_mark_read': 'events.mark_read',
}
for action, call in action_contracts.items():
    assert action in engine_text and call in engine_text, f'authorized dispatch missing: {action} -> {call}'
assert not re.search(r"connection\.execute\(\s*['\"](?:INSERT|UPDATE|DELETE)", engine_text, re.IGNORECASE), 'dispatcher contains direct mutating SQL'
for service_path in [
    '/home/ubuntu/brasfoot_engine/engine/stadiums/service.py',
    '/home/ubuntu/brasfoot_engine/engine/social/attendance.py',
    '/home/ubuntu/brasfoot_engine/engine/economy/staff_market.py',
    '/home/ubuntu/brasfoot_engine/engine/economy/sponsorships.py',
    '/home/ubuntu/brasfoot_engine/engine/world/weekly_cycle.py',
    '/home/ubuntu/brasfoot_engine/engine/events/service.py',
]:
    source = Path(service_path).read_text(encoding='utf-8')
    assert 'connection' in source and 'execute(' in source, f'SQL service lacks connection execute: {service_path}'

mutation_files = sorted((ROOT / 'server' / 'routers').glob('*.ts'))
for path in mutation_files:
    text = path.read_text(encoding='utf-8')
    if '.mutation' not in text:
        continue
    if path.name in {'events.ts', 'stadium.ts', 'sponsorship.ts', 'staffMarket.ts', 'career.ts'}:
        assert 'careerGateway' in text, f'mutation router without careerGateway import: {path}'

print('frontend-sem-write-check=ok')
print('mutation-gateway-contract=ok')
print('gateway-python-service-sql-chain=ok')
print({'mutation_routers_checked': len([p for p in mutation_files if '.mutation' in p.read_text(encoding='utf-8')]), 'authorized_dispatches_checked': len(action_contracts)})
