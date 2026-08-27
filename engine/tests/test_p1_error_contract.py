import sqlite3

import pytest

from engine.core.domain_errors import DomainError
from engine.core.p1_error_contract import audit_p1_errors, ensure_p1_error_registry, protect_p1_error_mutation, read_p1_errors, validate_p1_error


def test_p1_error_registry_is_idempotent_and_complete():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    ensure_p1_error_registry(connection)
    ensure_p1_error_registry(connection)
    assert len(read_p1_errors(connection)) == 10
    assert validate_p1_error(connection, 1061)['status'] == 'VALID'
    assert validate_p1_error(connection, 1070)['status'] == 'VALID'
    assert audit_p1_errors(connection)['status'] == 'VALID'


def test_p1_error_mutation_is_authorized_only_by_sql_service():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    ensure_p1_error_registry(connection)
    with pytest.raises(DomainError, match='P0_MUTATION_AUTHORIZATION_REQUIRED'):
        protect_p1_error_mutation(connection, 1061, 'FRONTEND', {'attempt': True})
    result = protect_p1_error_mutation(connection, 1061, 'AUTHORIZED_SQL_SERVICE', {'source': 'test'})
    assert result['allowed'] is True
    assert len(result['payload_hash']) == 64
