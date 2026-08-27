from pathlib import Path
p=Path('/home/ubuntu/brasfoot_engine/scripts/career_gateway.py')
s=p.read_text()
needle='from engine.core.p1_commission_contract import audit_p1_commissions, protect_p1_commission_mutation, read_p1_commissions, read_p1_commission_state, persist_p1_commission, validate_p1_commission\n'
s=s.replace(needle, needle+'from engine.core.p1_loan_contract import audit_p1_loans, protect_p1_loan_mutation, read_p1_loans, read_p1_loan_state, persist_p1_loan, validate_p1_loan\n',1)
needle='def p1_commission_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n'
fn="""def p1_loan_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n    if action == 'p1_loan_contracts': return {'items': read_p1_loans(connection), 'read_only': True}\n    if action == 'p1_loan_state': return {'items': read_p1_loan_state(connection, payload.get('loan_key')), 'read_only': True}\n    if action == 'p1_loan_validate': return validate_p1_loan(connection, int(payload.get('item_id')))\n    if action == 'p1_loan_persist': return persist_p1_loan(connection, str(payload.get('loan_key', '')), int(payload.get('loan_id', 0)), str(payload.get('loan_name', '')), dict(payload.get('loan_payload') or {}), payload.get('club_id'), str(payload.get('status', 'ACTIVE')), str(payload.get('actor', '')))\n    if action == 'p1_loan_protect': return protect_p1_loan_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))\n    if action == 'p1_loan_audit': return audit_p1_loans(connection)\n    raise ValueError('P1_LOAN_ACTION_INVALID')\n\n"""
s=s.replace(needle,fn+needle,1)
marker='        if action in {"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit"}:\n            return {"ok": True, **p1_commission_market(service.connection, action, payload)}\n'
s=s.replace(marker,marker+'        if action in {"p1_loan_contracts", "p1_loan_state", "p1_loan_validate", "p1_loan_persist", "p1_loan_protect", "p1_loan_audit"}:\n            return {"ok": True, **p1_loan_market(service.connection, action, payload)}\n',1)
choices='"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit", '
s=s.replace(choices,choices+'"p1_loan_contracts", "p1_loan_state", "p1_loan_validate", "p1_loan_persist", "p1_loan_protect", "p1_loan_audit", ',1)
p.write_text(s)
