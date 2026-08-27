import sqlite3

import pytest

from engine.core.domain_errors import DomainError
from engine.core.p1_preferences_contract import (
    ITEM_IDS,
    audit_p1_preferences,
    ensure_p1_preferences_registry,
    persist_p1_preferences,
    protect_p1_preferences_mutation,
    read_p1_preferences,
    read_p1_preferences_state,
    validate_p1_preferences,
)


def test_preferences_contract_is_idempotent_and_protected():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    ensure_p1_preferences_registry(connection)
    ensure_p1_preferences_registry(connection)
    assert len(read_p1_preferences(connection)) == 10
    assert all(validate_p1_preferences(connection, item_id)['status'] == 'VALID' for item_id in ITEM_IDS)
    with pytest.raises(DomainError):
        persist_p1_preferences(connection, 'main', 1, 'Preferências', {}, user_id=7, actor='FRONTEND')
    stored = persist_p1_preferences(connection, 'main', 1, 'Preferências', {'language': 'pt-BR'}, user_id=7, actor='AUTHORIZED_SQL_SERVICE')
    assert stored['payload_hash']
    assert read_p1_preferences_state(connection, 'main')[0]['preferences_name'] == 'Preferências'
    assert protect_p1_preferences_mutation(connection, 1295, 'AUTHORIZED_SQL_SERVICE', {})['allowed'] is True
    with pytest.raises(DomainError):
        protect_p1_preferences_mutation(connection, 1295, 'FRONTEND', {})
    assert audit_p1_preferences(connection)['status'] == 'VALID'
