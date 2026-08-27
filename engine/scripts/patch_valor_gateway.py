from pathlib import Path
p=Path('/home/ubuntu/brasfoot_engine/scripts/career_gateway.py')
s=p.read_text()
needle='from engine.core.p1_commission_contract import audit_p1_commissions, protect_p1_commission_mutation, read_p1_commissions, read_p1_commission_state, persist_p1_commission, validate_p1_commission\n'
s=s.replace(needle, needle+'from engine.core.p1_valor_contract import audit_p1_valors, protect_p1_valor_mutation, read_p1_valors, read_p1_valor_state, persist_p1_valor, validate_p1_valor\n',1)
needle='def p1_commission_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n'
fn="""def p1_valor_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n    if action == 'p1_valor_contracts': return {'items': read_p1_valors(connection), 'read_only': True}\n    if action == 'p1_valor_state': return {'items': read_p1_valor_state(connection, payload.get('valor_key')), 'read_only': True}\n    if action == 'p1_valor_validate': return validate_p1_valor(connection, int(payload.get('item_id')))\n    if action == 'p1_valor_persist': return persist_p1_valor(connection, str(payload.get('valor_key', '')), int(payload.get('valor_id', 0)), str(payload.get('valor_name', '')), dict(payload.get('valor_payload') or {}), payload.get('club_id'), str(payload.get('status', 'ACTIVE')), str(payload.get('actor', '')))\n    if action == 'p1_valor_protect': return protect_p1_valor_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))\n    if action == 'p1_valor_audit': return audit_p1_valors(connection)\n    raise ValueError('P1_VALOR_ACTION_INVALID')\n\n"""
s=s.replace(needle,fn+needle,1)
marker='        if action in {"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit"}:\n            return {"ok": True, **p1_commission_market(service.connection, action, payload)}\n'
s=s.replace(marker,marker+'        if action in {"p1_valor_contracts", "p1_valor_state", "p1_valor_validate", "p1_valor_persist", "p1_valor_protect", "p1_valor_audit"}:\n            return {"ok": True, **p1_valor_market(service.connection, action, payload)}\n',1)
choices='"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit", '
s=s.replace(choices,choices+'"p1_valor_contracts", "p1_valor_state", "p1_valor_validate", "p1_valor_persist", "p1_valor_protect", "p1_valor_audit", ',1)
p.write_text(s)
