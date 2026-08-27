import sqlite3

import pytest

from engine.core.domain_errors import DomainError
from engine.core.p1_stadium_contract import (
    ITEM_IDS,
    audit_p1_stadiums,
    ensure_p1_stadium_registry,
    persist_p1_stadium,
    protect_p1_stadium_mutation,
    read_p1_stadium_state,
    validate_p1_stadium,
)


def test_stadium_contract_is_idempotent_and_protected():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    ensure_p1_stadium_registry(connection)
    ensure_p1_stadium_registry(connection)
    assert [row['item_id'] for row in connection.execute('SELECT item_id FROM roadmap_p1_stadium_contracts ORDER BY item_id')] == list(ITEM_IDS)
    assert validate_p1_stadium(connection, 1301)['status'] == 'VALID'
    with pytest.raises(DomainError):
        persist_p1_stadium(connection, 'main', 1, 'Estádio principal', {'capacity': 50000}, club_id=10, actor='FRONTEND')
    result = persist_p1_stadium(connection, 'main', 1, 'Estádio principal', {'capacity': 50000}, club_id=10, actor='AUTHORIZED_SQL_SERVICE')
    assert result['payload_hash']
    same = persist_p1_stadium(connection, 'main', 1, 'Estádio principal', {'capacity': 50000}, club_id=10, actor='AUTHORIZED_SQL_SERVICE')
    assert same['payload_hash'] == result['payload_hash']
    assert len(read_p1_stadium_state(connection, 'main')) == 1
    with pytest.raises(DomainError):
        protect_p1_stadium_mutation(connection, 1301, 'FRONTEND', {'level': 2})
    assert protect_p1_stadium_mutation(connection, 1301, 'AUTHORIZED_SQL_SERVICE', {'level': 2})['allowed'] is True
    assert audit_p1_stadiums(connection)['status'] == 'VALID'
    connection.close()
