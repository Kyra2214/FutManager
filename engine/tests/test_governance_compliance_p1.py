import sqlite3
from engine.core.safe_undo import SafeUndoService


def test_confirmation_whitelist_undo_replay_and_compliance():
    connection = sqlite3.connect(':memory:')
    service = SafeUndoService(connection)
    item = service.register_training_plan(77)
    try:
        service.authorize('manager', 'TRAINING_PLAN_CANCEL', item['undo_id'], False)
    except ValueError as error:
        assert str(error) == 'CONFIRMATION_REQUIRED'
    else:
        raise AssertionError('confirmation bypassed')
    first = service.undo(item['undo_id'], 'manager', True)
    second = service.undo(item['undo_id'], 'manager', True)
    assert first['idempotent'] is False and second['idempotent'] is True
    report = service.compliance_report()
    assert report['persisted'] is True and report['replays'] == 1
    connection.close()
