from pathlib import Path

path = Path('/home/ubuntu/brasfoot_engine/scripts/career_gateway.py')
text = path.read_text()
text = text.replace(
    'from engine.core.p1_preferences_contract import audit_p1_preferences, protect_p1_preferences_mutation, read_p1_preferences, read_p1_preferences_state, persist_p1_preferences, validate_p1_preferences\n',
    'from engine.core.p1_preferences_contract import audit_p1_preferences, protect_p1_preferences_mutation, read_p1_preferences, read_p1_preferences_state, persist_p1_preferences, validate_p1_preferences\nfrom engine.core.p1_stadium_contract import audit_p1_stadiums, audit_p1_stadium_flow, protect_p1_stadium_mutation, read_p1_stadiums, read_p1_stadium_state, persist_p1_stadium, validate_p1_stadium\n'
)
anchor = "def p1_preferences_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n"
if 'def p1_stadium_market' not in text:
    start = text.index(anchor)
    next_def = text.index('\ndef ', start + 5)
    stadium = '''\ndef p1_stadium_market(connection: sqlite3.Connection, action: str, payload: dict) -> dict:\n    if action == 'p1_stadium_contracts': return {'items': read_p1_stadiums(connection), 'read_only': True}\n    if action == 'p1_stadium_state': return {'items': read_p1_stadium_state(connection, payload.get('stadium_key')), 'read_only': True}\n    if action == 'p1_stadium_validate': return validate_p1_stadium(connection, int(payload.get('item_id')))\n    if action == 'p1_stadium_persist': return persist_p1_stadium(connection, str(payload.get('stadium_key', '')), int(payload.get('stadium_id', 0)), str(payload.get('stadium_name', '')), dict(payload.get('stadium_payload') or {}), payload.get('club_id'), str(payload.get('status', 'ACTIVE')), str(payload.get('actor', '')))\n    if action == 'p1_stadium_protect': return protect_p1_stadium_mutation(connection, int(payload.get('item_id')), str(payload.get('actor', '')), dict(payload.get('mutation') or {}))\n    if action == 'p1_stadium_audit': return audit_p1_stadiums(connection)\n    raise ValueError('P1_STADIUM_ACTION_INVALID')\n'''
    text = text[:next_def] + stadium + text[next_def:]
needle = '        if action in {"p1_preferences_contracts", "p1_preferences_state", "p1_preferences_validate", "p1_preferences_persist", "p1_preferences_protect", "p1_preferences_audit"}:\n            return {"ok": True, **p1_preferences_market(service.connection, action, payload)}\n'
insert = needle + '        if action in {"p1_stadium_contracts", "p1_stadium_state", "p1_stadium_validate", "p1_stadium_persist", "p1_stadium_protect", "p1_stadium_audit"}:\n            return {"ok": True, **p1_stadium_market(service.connection, action, payload)}\n'
text = text.replace(needle, insert)
choice = '"p1_preferences_contracts", "p1_preferences_state", "p1_preferences_validate", "p1_preferences_persist", "p1_preferences_protect", "p1_preferences_audit", '
text = text.replace(choice, choice + '"p1_stadium_contracts", "p1_stadium_state", "p1_stadium_validate", "p1_stadium_persist", "p1_stadium_protect", "p1_stadium_audit", ')
path.write_text(text)
