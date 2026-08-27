from pathlib import Path
p=Path('/home/ubuntu/brasfoot_engine/scripts/career_gateway.py')
s=p.read_text()
needle='from engine.core.p1_commission_contract import audit_p1_commissions, protect_p1_commission_mutation, read_p1_commissions, read_p1_commission_state, persist_p1_commission, validate_p1_commission\n'
s=s.replace(needle, needle+'from engine.core.p1_sale_contract import audit_p1_sales, protect_p1_sale_mutation, read_p1_sales, read_p1_sale_state, persist_p1_sale, validate_p1_sale\n',1)
needle='def p1_commission_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n'
fn="""def p1_sale_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n    if action == 'p1_sale_contracts': return {'items': read_p1_sales(connection), 'read_only': True}\n    if action == 'p1_sale_state': return {'items': read_p1_sale_state(connection, payload.get('sale_key')), 'read_only': True}\n    if action == 'p1_sale_validate': return validate_p1_sale(connection, int(payload.get('item_id')))\n    if action == 'p1_sale_persist': return persist_p1_sale(connection, str(payload.get('sale_key', '')), int(payload.get('sale_id', 0)), str(payload.get('sale_name', '')), dict(payload.get('sale_payload') or {}), payload.get('club_id'), str(payload.get('status', 'ACTIVE')), str(payload.get('actor', '')))\n    if action == 'p1_sale_protect': return protect_p1_sale_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))\n    if action == 'p1_sale_audit': return audit_p1_sales(connection)\n    raise ValueError('P1_SALE_ACTION_INVALID')\n\n"""
s=s.replace(needle,fn+needle,1)
marker='        if action in {"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit"}:\n            return {"ok": True, **p1_commission_market(service.connection, action, payload)}\n'
s=s.replace(marker,marker+'        if action in {"p1_sale_contracts", "p1_sale_state", "p1_sale_validate", "p1_sale_persist", "p1_sale_protect", "p1_sale_audit"}:\n            return {"ok": True, **p1_sale_market(service.connection, action, payload)}\n',1)
choices='"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit", '
s=s.replace(choices,choices+'"p1_sale_contracts", "p1_sale_state", "p1_sale_validate", "p1_sale_persist", "p1_sale_protect", "p1_sale_audit", ',1)
p.write_text(s)
