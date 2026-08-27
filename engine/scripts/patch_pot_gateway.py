from pathlib import Path
p=Path('/home/ubuntu/brasfoot_engine/scripts/career_gateway.py')
s=p.read_text()
needle='from engine.core.p1_commission_contract import audit_p1_commissions, protect_p1_commission_mutation, read_p1_commissions, read_p1_commission_state, persist_p1_commission, validate_p1_commission\n'
s=s.replace(needle, needle+'from engine.core.p1_pot_contract import audit_p1_pots, protect_p1_pot_mutation, read_p1_pots, read_p1_pot_state, persist_p1_pot, validate_p1_pot\n',1)
needle='def p1_commission_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n'
fn="""def p1_pot_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n    if action == 'p1_pot_contracts': return {'items': read_p1_pots(connection), 'read_only': True}\n    if action == 'p1_pot_state': return {'items': read_p1_pot_state(connection, payload.get('pot_key')), 'read_only': True}\n    if action == 'p1_pot_validate': return validate_p1_pot(connection, int(payload.get('item_id')))\n    if action == 'p1_pot_persist': return persist_p1_pot(connection, str(payload.get('pot_key', '')), int(payload.get('pot_id', 0)), str(payload.get('pot_name', '')), dict(payload.get('pot_payload') or {}), payload.get('club_id'), str(payload.get('status', 'ACTIVE')), str(payload.get('actor', '')))\n    if action == 'p1_pot_protect': return protect_p1_pot_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))\n    if action == 'p1_pot_audit': return audit_p1_pots(connection)\n    raise ValueError('P1_POT_ACTION_INVALID')\n\n"""
s=s.replace(needle,fn+needle,1)
marker='        if action in {"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit"}:\n            return {"ok": True, **p1_commission_market(service.connection, action, payload)}\n'
s=s.replace(marker,marker+'        if action in {"p1_pot_contracts", "p1_pot_state", "p1_pot_validate", "p1_pot_persist", "p1_pot_protect", "p1_pot_audit"}:\n            return {"ok": True, **p1_pot_market(service.connection, action, payload)}\n',1)
choices='"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit", '
s=s.replace(choices,choices+'"p1_pot_contracts", "p1_pot_state", "p1_pot_validate", "p1_pot_persist", "p1_pot_protect", "p1_pot_audit", ',1)
p.write_text(s)
