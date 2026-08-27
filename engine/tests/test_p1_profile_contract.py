import sqlite3

import pytest

from engine.core.domain_errors import DomainError
from engine.core.p1_profile_contract import (
    ITEM_IDS,
    audit_p1_profiles,
    ensure_p1_profile_registry,
    persist_p1_profile,
    protect_p1_profile_mutation,
    read_p1_profile_state,
    read_p1_profiles,
    validate_p1_profile,
)


def test_profile_contract_is_idempotent_and_protected():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    ensure_p1_profile_registry(connection)
    ensure_p1_profile_registry(connection)
    assert len(read_p1_profiles(connection)) == 10
    assert all(validate_p1_profile(connection, item_id)['status'] == 'VALID' for item_id in ITEM_IDS)
    with pytest.raises(DomainError):
        persist_p1_profile(connection, 'main', 1, 'Perfil', {}, manager_id=7, actor='FRONTEND')
    stored = persist_p1_profile(connection, 'main', 1, 'Perfil', {'age': 30}, manager_id=7, actor='AUTHORIZED_SQL_SERVICE')
    assert stored['payload_hash']
    assert read_p1_profile_state(connection, 'main')[0]['profile_name'] == 'Perfil'
    assert protect_p1_profile_mutation(connection, 1285, 'AUTHORIZED_SQL_SERVICE', {})['allowed'] is True
    with pytest.raises(DomainError):
        protect_p1_profile_mutation(connection, 1285, 'FRONTEND', {})
    assert audit_p1_profiles(connection)['status'] == 'VALID'
