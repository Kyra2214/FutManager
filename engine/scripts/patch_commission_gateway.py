from pathlib import Path
p = Path('/home/ubuntu/brasfoot_engine/scripts/career_gateway.py')
s = p.read_text()
needle = 'def p1_fifa_date_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n'
fn = """def p1_commission_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n    if action == 'p1_commission_contracts': return {'items': read_p1_commissions(connection), 'read_only': True}\n    if action == 'p1_commission_state': return {'items': read_p1_commission_state(connection, payload.get('commission_key')), 'read_only': True}\n    if action == 'p1_commission_validate': return validate_p1_commission(connection, int(payload.get('item_id')))\n    if action == 'p1_commission_persist': return persist_p1_commission(connection, str(payload.get('commission_key', '')), int(payload.get('commission_id', 0)), str(payload.get('commission_name', '')), dict(payload.get('commission_payload') or {}), payload.get('club_id'), str(payload.get('status', 'ACTIVE')), str(payload.get('actor', '')))\n    if action == 'p1_commission_protect': return protect_p1_commission_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))\n    if action == 'p1_commission_audit': return audit_p1_commissions(connection)\n    raise ValueError('P1_COMMISSION_ACTION_INVALID')\n\n"""
if 'def p1_commission_market' not in s:
    s = s.replace(needle, fn + needle, 1)
needle2 = 'from engine.core.p1_fifa_date_contract import audit_p1_fifa_dates, protect_p1_fifa_date_mutation, read_p1_fifa_dates, read_p1_fifa_date_state, persist_p1_fifa_date, validate_p1_fifa_date\n'
imp = needle2 + 'from engine.core.p1_commission_contract import audit_p1_commissions, protect_p1_commission_mutation, read_p1_commissions, read_p1_commission_state, persist_p1_commission, validate_p1_commission\n'
s = s.replace(needle2, imp, 1)
marker = '        if action in {"p1_fifa_date_contracts", "p1_fifa_date_state", "p1_fifa_date_validate", "p1_fifa_date_persist", "p1_fifa_date_protect", "p1_fifa_date_audit"}:\n            return {"ok": True, **p1_fifa_date_market(service.connection, action, payload)}\n'
insert = marker + '        if action in {"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit"}:\n            return {"ok": True, **p1_commission_market(service.connection, action, payload)}\n'
s = s.replace(marker, insert, 1)
choices = '"p1_fifa_date_contracts", "p1_fifa_date_state", "p1_fifa_date_validate", "p1_fifa_date_persist", "p1_fifa_date_protect", "p1_fifa_date_audit", '
s = s.replace(choices, choices + '"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit", ', 1)
p.write_text(s)
