from pathlib import Path

p = Path('/home/ubuntu/brasfoot_engine/scripts/career_gateway.py')
s = p.read_text()
needle = 'from engine.core.p1_commission_contract import audit_p1_commissions, protect_p1_commission_mutation, read_p1_commissions, read_p1_commission_state, persist_p1_commission, validate_p1_commission\n'
imp = 'from engine.core.p1_estrela_contract import audit_p1_estrelas, protect_p1_estrela_mutation, read_p1_estrelas, read_p1_estrela_state, persist_p1_estrela, validate_p1_estrela\n'
if 'from engine.core.p1_estrela_contract import' not in s:
    s = s.replace(needle, needle + imp, 1)
fn = '''def p1_estrela_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n    if action == 'p1_estrela_contracts': return {'items': read_p1_estrelas(connection), 'read_only': True}\n    if action == 'p1_estrela_state': return {'items': read_p1_estrela_state(connection, payload.get('star_rating')), 'read_only': True}\n    if action == 'p1_estrela_validate': return validate_p1_estrela(connection, int(payload.get('item_id')))\n    if action == 'p1_estrela_persist': return persist_p1_estrela(connection, int(payload.get('star_rating')), dict(payload.get('star_payload') or {}), str(payload.get('actor', '')))\n    if action == 'p1_estrela_protect': return protect_p1_estrela_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))\n    if action == 'p1_estrela_audit': return audit_p1_estrelas(connection)\n    raise ValueError('P1_ESTRELA_ACTION_INVALID')\n\n'''
needle_fn = 'def p1_commission_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n'
if 'def p1_estrela_market' not in s:
    s = s.replace(needle_fn, fn + needle_fn, 1)
marker = '        if action in {"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit"}:\n            return {"ok": True, **p1_commission_market(service.connection, action, payload)}\n'
route = '        if action in {"p1_estrela_contracts", "p1_estrela_state", "p1_estrela_validate", "p1_estrela_persist", "p1_estrela_protect", "p1_estrela_audit"}:\n            return {"ok": True, **p1_estrela_market(service.connection, action, payload)}\n'
if 'p1_estrela_market(service.connection' not in s:
    s = s.replace(marker, marker + route, 1)
choices = '"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit", '
if '"p1_estrela_contracts"' not in s:
    s = s.replace(choices, choices + '"p1_estrela_contracts", "p1_estrela_state", "p1_estrela_validate", "p1_estrela_persist", "p1_estrela_protect", "p1_estrela_audit", ', 1)
p.write_text(s)
