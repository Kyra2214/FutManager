import sqlite3

import pytest

from engine.core.domain_errors import DomainError
from engine.core.p1_regulation_contract import (
    ITEM_IDS,
    audit_p1_regulations,
    ensure_p1_regulation_registry,
    persist_p1_regulation,
    protect_p1_regulation_mutation,
    read_p1_regulation_state,
    validate_p1_regulation,
)


def test_regulation_contract_is_idempotent_and_protected():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    ensure_p1_regulation_registry(connection)
    ensure_p1_regulation_registry(connection)
    assert [r['item_id'] for r in connection.execute('SELECT item_id FROM roadmap_p1_regulation_contracts ORDER BY item_id')] == list(ITEM_IDS)
    assert validate_p1_regulation(connection, 1561)['status'] == 'VALID'
    with pytest.raises(DomainError):
        persist_p1_regulation(connection, 'main-capacity', 1, 'Capacidade principal', {'capacity': 50000}, club_id=10, actor='FRONTEND')
    result = persist_p1_regulation(connection, 'main-capacity', 1, 'Capacidade principal', {'capacity': 50000}, club_id=10, actor='AUTHORIZED_SQL_SERVICE')
    same = persist_p1_regulation(connection, 'main-capacity', 1, 'Capacidade principal', {'capacity': 50000}, club_id=10, actor='AUTHORIZED_SQL_SERVICE')
    assert same['payload_hash'] == result['payload_hash']
    assert len(read_p1_regulation_state(connection, 'main-capacity')) == 1
    with pytest.raises(DomainError):
        protect_p1_regulation_mutation(connection, 1561, 'FRONTEND', {'capacity': 60000})
    assert protect_p1_regulation_mutation(connection, 1561, 'AUTHORIZED_SQL_SERVICE', {'capacity': 60000})['allowed'] is True
    assert audit_p1_regulations(connection)['status'] == 'VALID'
