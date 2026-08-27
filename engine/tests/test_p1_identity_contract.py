import sqlite3

import pytest

from engine.core.domain_errors import DomainError
from engine.core.p1_identity_contract import (
    ITEM_IDS,
    audit_p1_identities,
    ensure_p1_identity_registry,
    persist_p1_identity,
    protect_p1_identity_mutation,
    read_p1_identity_state,
    read_p1_identities,
    validate_p1_identity,
)


def test_identity_contract_is_idempotent_and_protected():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    ensure_p1_identity_registry(connection)
    ensure_p1_identity_registry(connection)
    assert len(read_p1_identities(connection)) == 10
    assert all(validate_p1_identity(connection, item_id)['status'] == 'VALID' for item_id in ITEM_IDS)
    with pytest.raises(DomainError):
        persist_p1_identity(connection, 'manager', 1, 'Manager', {}, subject_id=7, actor='FRONTEND')
    stored = persist_p1_identity(connection, 'manager', 1, 'Manager', {'verified': True}, subject_id=7, actor='AUTHORIZED_SQL_SERVICE')
    assert stored['payload_hash']
    assert read_p1_identity_state(connection, 'manager')[0]['identity_name'] == 'Manager'
    assert protect_p1_identity_mutation(connection, 1275, 'AUTHORIZED_SQL_SERVICE', {})['allowed'] is True
    with pytest.raises(DomainError):
        protect_p1_identity_mutation(connection, 1275, 'FRONTEND', {})
    assert audit_p1_identities(connection)['status'] == 'VALID'
