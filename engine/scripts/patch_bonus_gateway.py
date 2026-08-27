from pathlib import Path
p=Path('/home/ubuntu/brasfoot_engine/scripts/career_gateway.py')
s=p.read_text()
needle='from engine.core.p1_commission_contract import audit_p1_commissions, protect_p1_commission_mutation, read_p1_commissions, read_p1_commission_state, persist_p1_commission, validate_p1_commission\n'
s=s.replace(needle, needle+'from engine.core.p1_bonus_contract import audit_p1_bonuss, protect_p1_bonus_mutation, read_p1_bonuss, read_p1_bonus_state, persist_p1_bonus, validate_p1_bonus\n',1)
needle='def p1_commission_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n'
fn="""def p1_bonus_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n    if action == 'p1_bonus_contracts': return {'items': read_p1_bonuss(connection), 'read_only': True}\n    if action == 'p1_bonus_state': return {'items': read_p1_bonus_state(connection, payload.get('bonus_key')), 'read_only': True}\n    if action == 'p1_bonus_validate': return validate_p1_bonus(connection, int(payload.get('item_id')))\n    if action == 'p1_bonus_persist': return persist_p1_bonus(connection, str(payload.get('bonus_key', '')), int(payload.get('bonus_id', 0)), str(payload.get('bonus_name', '')), dict(payload.get('bonus_payload') or {}), payload.get('club_id'), str(payload.get('status', 'ACTIVE')), str(payload.get('actor', '')))\n    if action == 'p1_bonus_protect': return protect_p1_bonus_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))\n    if action == 'p1_bonus_audit': return audit_p1_bonuss(connection)\n    raise ValueError('P1_BONUS_ACTION_INVALID')\n\n"""
s=s.replace(needle,fn+needle,1)
marker='        if action in {"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit"}:\n            return {"ok": True, **p1_commission_market(service.connection, action, payload)}\n'
s=s.replace(marker,marker+'        if action in {"p1_bonus_contracts", "p1_bonus_state", "p1_bonus_validate", "p1_bonus_persist", "p1_bonus_protect", "p1_bonus_audit"}:\n            return {"ok": True, **p1_bonus_market(service.connection, action, payload)}\n',1)
choices='"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit", '
s=s.replace(choices,choices+'"p1_bonus_contracts", "p1_bonus_state", "p1_bonus_validate", "p1_bonus_persist", "p1_bonus_protect", "p1_bonus_audit", ',1)
p.write_text(s)
