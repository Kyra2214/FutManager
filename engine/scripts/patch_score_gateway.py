from pathlib import Path
p=Path('/home/ubuntu/brasfoot_engine/scripts/career_gateway.py')
s=p.read_text()
needle='from engine.core.p1_commission_contract import audit_p1_commissions, protect_p1_commission_mutation, read_p1_commissions, read_p1_commission_state, persist_p1_commission, validate_p1_commission\n'
s=s.replace(needle, needle+'from engine.core.p1_score_contract import audit_p1_scores, protect_p1_score_mutation, read_p1_scores, read_p1_score_state, persist_p1_score, validate_p1_score\n',1)
needle='def p1_commission_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n'
fn="""def p1_score_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n    if action == 'p1_score_contracts': return {'items': read_p1_scores(connection), 'read_only': True}\n    if action == 'p1_score_state': return {'items': read_p1_score_state(connection, payload.get('score_key')), 'read_only': True}\n    if action == 'p1_score_validate': return validate_p1_score(connection, int(payload.get('item_id')))\n    if action == 'p1_score_persist': return persist_p1_score(connection, str(payload.get('score_key', '')), int(payload.get('score_id', 0)), str(payload.get('score_name', '')), dict(payload.get('score_payload') or {}), payload.get('club_id'), str(payload.get('status', 'ACTIVE')), str(payload.get('actor', '')))\n    if action == 'p1_score_protect': return protect_p1_score_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))\n    if action == 'p1_score_audit': return audit_p1_scores(connection)\n    raise ValueError('P1_SCORE_ACTION_INVALID')\n\n"""
s=s.replace(needle,fn+needle,1)
marker='        if action in {"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit"}:\n            return {"ok": True, **p1_commission_market(service.connection, action, payload)}\n'
s=s.replace(marker,marker+'        if action in {"p1_score_contracts", "p1_score_state", "p1_score_validate", "p1_score_persist", "p1_score_protect", "p1_score_audit"}:\n            return {"ok": True, **p1_score_market(service.connection, action, payload)}\n',1)
choices='"p1_commission_contracts", "p1_commission_state", "p1_commission_validate", "p1_commission_persist", "p1_commission_protect", "p1_commission_audit", '
s=s.replace(choices,choices+'"p1_score_contracts", "p1_score_state", "p1_score_validate", "p1_score_persist", "p1_score_protect", "p1_score_audit", ',1)
p.write_text(s)
