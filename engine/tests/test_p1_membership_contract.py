import sqlite3

import pytest

from engine.core.domain_errors import DomainError
from engine.core.p1_membership_contract import (
    ITEM_IDS,
    audit_p1_memberships,
    ensure_p1_membership_registry,
    persist_p1_membership,
    protect_p1_membership_mutation,
    read_p1_membership_state,
    validate_p1_membership,
)


def test_membership_contract_is_idempotent_and_protected():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    ensure_p1_membership_registry(connection)
    ensure_p1_membership_registry(connection)
    assert [r['item_id'] for r in connection.execute('SELECT item_id FROM roadmap_p1_membership_contracts ORDER BY item_id')] == list(ITEM_IDS)
    assert validate_p1_membership(connection, 1551)['status'] == 'VALID'
    with pytest.raises(DomainError):
        persist_p1_membership(connection, 'main-capacity', 1, 'Capacidade principal', {'capacity': 50000}, club_id=10, actor='FRONTEND')
    result = persist_p1_membership(connection, 'main-capacity', 1, 'Capacidade principal', {'capacity': 50000}, club_id=10, actor='AUTHORIZED_SQL_SERVICE')
    same = persist_p1_membership(connection, 'main-capacity', 1, 'Capacidade principal', {'capacity': 50000}, club_id=10, actor='AUTHORIZED_SQL_SERVICE')
    assert same['payload_hash'] == result['payload_hash']
    assert len(read_p1_membership_state(connection, 'main-capacity')) == 1
    with pytest.raises(DomainError):
        protect_p1_membership_mutation(connection, 1551, 'FRONTEND', {'capacity': 60000})
    assert protect_p1_membership_mutation(connection, 1551, 'AUTHORIZED_SQL_SERVICE', {'capacity': 60000})['allowed'] is True
    assert audit_p1_memberships(connection)['status'] == 'VALID'
