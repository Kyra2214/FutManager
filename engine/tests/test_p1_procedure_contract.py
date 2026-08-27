import sqlite3

import pytest

from engine.core.domain_errors import DomainError
from engine.core.p1_procedure_contract import audit_p1_procedures, ensure_p1_procedure_registry, protect_p1_procedure_mutation, read_p1_procedures, validate_p1_procedure


def test_p1_procedure_registry_is_idempotent_and_complete():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    ensure_p1_procedure_registry(connection)
    ensure_p1_procedure_registry(connection)
    assert len(read_p1_procedures(connection)) == 10
    assert validate_p1_procedure(connection, 1051)['status'] == 'VALID'
    assert validate_p1_procedure(connection, 1060)['status'] == 'VALID'
    assert audit_p1_procedures(connection)['status'] == 'VALID'


def test_p1_procedure_mutation_is_authorized_only_by_sql_service():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    ensure_p1_procedure_registry(connection)
    with pytest.raises(DomainError, match='P0_MUTATION_AUTHORIZATION_REQUIRED'):
        protect_p1_procedure_mutation(connection, 1051, 'FRONTEND', {'attempt': True})
    result = protect_p1_procedure_mutation(connection, 1051, 'AUTHORIZED_SQL_SERVICE', {'source': 'test'})
    assert result['allowed'] is True
    assert len(result['payload_hash']) == 64
