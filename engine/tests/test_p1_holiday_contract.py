import sqlite3

import pytest

from engine.core.domain_errors import DomainError
from engine.core.p1_holiday_contract import (
    ITEM_IDS,
    audit_p1_holidays,
    ensure_p1_holiday_registry,
    persist_p1_holiday,
    protect_p1_holiday_mutation,
    read_p1_holiday_state,
    validate_p1_holiday,
)


def test_holiday_contract_is_idemholidayent_and_protected():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    ensure_p1_holiday_registry(connection)
    ensure_p1_holiday_registry(connection)
    assert [r['item_id'] for r in connection.execute('SELECT item_id FROM roadmap_p1_holiday_contracts ORDER BY item_id')] == list(ITEM_IDS)
    assert validate_p1_holiday(connection, 1851)['status'] == 'VALID'
    with pytest.raises(DomainError):
        persist_p1_holiday(connection, 'main-capacity', 1, 'Capacidade principal', {'capacity': 50000}, club_id=10, actor='FRONTEND')
    result = persist_p1_holiday(connection, 'main-capacity', 1, 'Capacidade principal', {'capacity': 50000}, club_id=10, actor='AUTHORIZED_SQL_SERVICE')
    same = persist_p1_holiday(connection, 'main-capacity', 1, 'Capacidade principal', {'capacity': 50000}, club_id=10, actor='AUTHORIZED_SQL_SERVICE')
    assert same['payload_hash'] == result['payload_hash']
    assert len(read_p1_holiday_state(connection, 'main-capacity')) == 1
    with pytest.raises(DomainError):
        protect_p1_holiday_mutation(connection, 1851, 'FRONTEND', {'capacity': 60000})
    assert protect_p1_holiday_mutation(connection, 1851, 'AUTHORIZED_SQL_SERVICE', {'capacity': 60000})['allowed'] is True
    assert audit_p1_holidays(connection)['status'] == 'VALID'
