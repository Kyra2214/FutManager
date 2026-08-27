from pathlib import Path
p=Path('/home/ubuntu/brasfoot_engine/scripts/career_gateway.py')
s=p.read_text()
needle='from engine.core.p1_commission_contract import audit_p1_commissions, protect_p1_commission_mutation, read_p1_commissions, read_p1_commission_state, persist_p1_commission, validate_p1_commission\n'
s=s.replace(needle, needle+'from engine.core.p1_event_contract import audit_p1_events, protect_p1_event_mutation, read_p1_events, read_p1_event_state, persist_p1_event, validate_p1_event\n',1)
needle='def p1_commission_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n'
fn="""def p1_event_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n    if action == 'p1_event_contracts': return {'items': read_p1_events(connection), 'read_only': True}\n    if action == 'p1_event_state': return {'items': read_p1_event_state(connection, payload.get('event_key')), 'read_only': True}\n    if action == 'p1_event_validate': return validate_p1_event(connection, int(payload.get('item_id')))\n    if action == 'p1_event_persist': return persist_p1_event(connection, str(payload.get('event_key', '')), int(payload.get('event_id', 0)), str(payload.get('event_name', '')), dict(payload.get('event_payload') or {}), payload.get('club_id'), str(payload.get('status', 'ACTIVE')), str(payload.get('actor', '')))\n    if action == 'p1_event_protect': return protect_p1_event_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))\n    if action == 'p1_event_audit': return audit_p1_events(connection)\n    raise ValueError('P1_EVENT_ACTION_INVALID')\n\n"""
s=s.replace(needle,fn+needle,1)
marker='        if action in {"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit"}:\n            return {"ok": True, **p1_commission_market(service.connection, action, payload)}\n'
s=s.replace(marker,marker+'        if action in {"p1_event_contracts", "p1_event_state", "p1_event_validate", "p1_event_persist", "p1_event_protect", "p1_event_audit"}:\n            return {"ok": True, **p1_event_market(service.connection, action, payload)}\n',1)
choices='"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit", '
s=s.replace(choices,choices+'"p1_event_contracts", "p1_event_state", "p1_event_validate", "p1_event_persist", "p1_event_protect", "p1_event_audit", ',1)
p.write_text(s)
