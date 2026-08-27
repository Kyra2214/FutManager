import sqlite3

import pytest

from engine.core.domain_errors import DomainError
from engine.core.p1_knockout_contract import (
    ITEM_IDS,
    audit_p1_knockouts,
    ensure_p1_knockout_registry,
    persist_p1_knockout,
    protect_p1_knockout_mutation,
    read_p1_knockout_state,
    validate_p1_knockout,
)


def test_knockout_contract_is_idemknockoutent_and_protected():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    ensure_p1_knockout_registry(connection)
    ensure_p1_knockout_registry(connection)
    assert [r['item_id'] for r in connection.execute('SELECT item_id FROM roadmap_p1_knockout_contracts ORDER BY item_id')] == list(ITEM_IDS)
    assert validate_p1_knockout(connection, 1771)['status'] == 'VALID'
    with pytest.raises(DomainError):
        persist_p1_knockout(connection, 'main-capacity', 1, 'Capacidade principal', {'capacity': 50000}, club_id=10, actor='FRONTEND')
    result = persist_p1_knockout(connection, 'main-capacity', 1, 'Capacidade principal', {'capacity': 50000}, club_id=10, actor='AUTHORIZED_SQL_SERVICE')
    same = persist_p1_knockout(connection, 'main-capacity', 1, 'Capacidade principal', {'capacity': 50000}, club_id=10, actor='AUTHORIZED_SQL_SERVICE')
    assert same['payload_hash'] == result['payload_hash']
    assert len(read_p1_knockout_state(connection, 'main-capacity')) == 1
    with pytest.raises(DomainError):
        protect_p1_knockout_mutation(connection, 1771, 'FRONTEND', {'capacity': 60000})
    assert protect_p1_knockout_mutation(connection, 1771, 'AUTHORIZED_SQL_SERVICE', {'capacity': 60000})['allowed'] is True
    assert audit_p1_knockouts(connection)['status'] == 'VALID'
