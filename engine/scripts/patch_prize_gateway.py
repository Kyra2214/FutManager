from pathlib import Path
p=Path('/home/ubuntu/brasfoot_engine/scripts/career_gateway.py')
s=p.read_text()
needle='from engine.core.p1_commission_contract import audit_p1_commissions, protect_p1_commission_mutation, read_p1_commissions, read_p1_commission_state, persist_p1_commission, validate_p1_commission\n'
s=s.replace(needle, needle+'from engine.core.p1_prize_contract import audit_p1_prizes, protect_p1_prize_mutation, read_p1_prizes, read_p1_prize_state, persist_p1_prize, validate_p1_prize\n',1)
needle='def p1_commission_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n'
fn="""def p1_prize_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n    if action == 'p1_prize_contracts': return {'items': read_p1_prizes(connection), 'read_only': True}\n    if action == 'p1_prize_state': return {'items': read_p1_prize_state(connection, payload.get('prize_key')), 'read_only': True}\n    if action == 'p1_prize_validate': return validate_p1_prize(connection, int(payload.get('item_id')))\n    if action == 'p1_prize_persist': return persist_p1_prize(connection, str(payload.get('prize_key', '')), int(payload.get('prize_id', 0)), str(payload.get('prize_name', '')), dict(payload.get('prize_payload') or {}), payload.get('club_id'), str(payload.get('status', 'ACTIVE')), str(payload.get('actor', '')))\n    if action == 'p1_prize_protect': return protect_p1_prize_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))\n    if action == 'p1_prize_audit': return audit_p1_prizes(connection)\n    raise ValueError('P1_PRIZE_ACTION_INVALID')\n\n"""
s=s.replace(needle,fn+needle,1)
marker='        if action in {"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit"}:\n            return {"ok": True, **p1_commission_market(service.connection, action, payload)}\n'
s=s.replace(marker,marker+'        if action in {"p1_prize_contracts", "p1_prize_state", "p1_prize_validate", "p1_prize_persist", "p1_prize_protect", "p1_prize_audit"}:\n            return {"ok": True, **p1_prize_market(service.connection, action, payload)}\n',1)
choices='"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit", '
s=s.replace(choices,choices+'"p1_prize_contracts", "p1_prize_state", "p1_prize_validate", "p1_prize_persist", "p1_prize_protect", "p1_prize_audit", ',1)
p.write_text(s)
