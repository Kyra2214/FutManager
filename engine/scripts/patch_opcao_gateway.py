from pathlib import Path
p=Path('/home/ubuntu/brasfoot_engine/scripts/career_gateway.py')
s=p.read_text()
needle='from engine.core.p1_commission_contract import audit_p1_commissions, protect_p1_commission_mutation, read_p1_commissions, read_p1_commission_state, persist_p1_commission, validate_p1_commission\n'
s=s.replace(needle, needle+'from engine.core.p1_opcao_contract import audit_p1_opcaos, protect_p1_opcao_mutation, read_p1_opcaos, read_p1_opcao_state, persist_p1_opcao, validate_p1_opcao\n',1)
needle='def p1_commission_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n'
fn="""def p1_opcao_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n    if action == 'p1_opcao_contracts': return {'items': read_p1_opcaos(connection), 'read_only': True}\n    if action == 'p1_opcao_state': return {'items': read_p1_opcao_state(connection, payload.get('opcao_key')), 'read_only': True}\n    if action == 'p1_opcao_validate': return validate_p1_opcao(connection, int(payload.get('item_id')))\n    if action == 'p1_opcao_persist': return persist_p1_opcao(connection, str(payload.get('opcao_key', '')), int(payload.get('opcao_id', 0)), str(payload.get('opcao_name', '')), dict(payload.get('opcao_payload') or {}), payload.get('club_id'), str(payload.get('status', 'ACTIVE')), str(payload.get('actor', '')))\n    if action == 'p1_opcao_protect': return protect_p1_opcao_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))\n    if action == 'p1_opcao_audit': return audit_p1_opcaos(connection)\n    raise ValueError('P1_OPCAO_ACTION_INVALID')\n\n"""
s=s.replace(needle,fn+needle,1)
marker='        if action in {"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit"}:\n            return {"ok": True, **p1_commission_market(service.connection, action, payload)}\n'
s=s.replace(marker,marker+'        if action in {"p1_opcao_contracts", "p1_opcao_state", "p1_opcao_validate", "p1_opcao_persist", "p1_opcao_protect", "p1_opcao_audit"}:\n            return {"ok": True, **p1_opcao_market(service.connection, action, payload)}\n',1)
choices='"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit", '
s=s.replace(choices,choices+'"p1_opcao_contracts", "p1_opcao_state", "p1_opcao_validate", "p1_opcao_persist", "p1_opcao_protect", "p1_opcao_audit", ',1)
p.write_text(s)
