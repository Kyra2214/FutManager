from pathlib import Path
p=Path('/home/ubuntu/brasfoot_engine/scripts/career_gateway.py')
s=p.read_text()
needle='from engine.core.p1_commission_contract import audit_p1_commissions, protect_p1_commission_mutation, read_p1_commissions, read_p1_commission_state, persist_p1_commission, validate_p1_commission\n'
s=s.replace(needle, needle+'from engine.core.p1_group_contract import audit_p1_groups, protect_p1_group_mutation, read_p1_groups, read_p1_group_state, persist_p1_group, validate_p1_group\n',1)
needle='def p1_commission_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n'
fn="""def p1_group_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n    if action == 'p1_group_contracts': return {'items': read_p1_groups(connection), 'read_only': True}\n    if action == 'p1_group_state': return {'items': read_p1_group_state(connection, payload.get('group_key')), 'read_only': True}\n    if action == 'p1_group_validate': return validate_p1_group(connection, int(payload.get('item_id')))\n    if action == 'p1_group_persist': return persist_p1_group(connection, str(payload.get('group_key', '')), int(payload.get('group_id', 0)), str(payload.get('group_name', '')), dict(payload.get('group_payload') or {}), payload.get('club_id'), str(payload.get('status', 'ACTIVE')), str(payload.get('actor', '')))\n    if action == 'p1_group_protect': return protect_p1_group_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))\n    if action == 'p1_group_audit': return audit_p1_groups(connection)\n    raise ValueError('P1_GROUP_ACTION_INVALID')\n\n"""
s=s.replace(needle,fn+needle,1)
marker='        if action in {"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit"}:\n            return {"ok": True, **p1_commission_market(service.connection, action, payload)}\n'
s=s.replace(marker,marker+'        if action in {"p1_group_contracts", "p1_group_state", "p1_group_validate", "p1_group_persist", "p1_group_protect", "p1_group_audit"}:\n            return {"ok": True, **p1_group_market(service.connection, action, payload)}\n',1)
choices='"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit", '
s=s.replace(choices,choices+'"p1_group_contracts", "p1_group_state", "p1_group_validate", "p1_group_persist", "p1_group_protect", "p1_group_audit", ',1)
p.write_text(s)
