import sqlite3

import pytest

from engine.core.domain_errors import DomainError
from engine.core.p0_contracts import audit_p0_contracts, ensure_p0_contract_registry, protect_p0_mutation, read_p0_contracts, validate_p0_contract


def test_p0_registry_has_exactly_300_sql_contracts():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    ensure_p0_contract_registry(connection)
    assert len(read_p0_contracts(connection)) == 300
    assert validate_p0_contract(connection, 941)['status'] == 'VALID'
    assert validate_p0_contract(connection, 3850)['status'] == 'VALID'
    audit = audit_p0_contracts(connection)
    assert audit['status'] == 'VALID'
    assert audit['contract_count'] == 300
    assert audit['read_only'] is True


def test_p0_mutation_requires_authorized_sql_service():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    ensure_p0_contract_registry(connection)
    with pytest.raises(DomainError, match='P0_MUTATION_AUTHORIZATION_REQUIRED'):
        protect_p0_mutation(connection, 941, 'FRONTEND', {'attempt': True})
    result = protect_p0_mutation(connection, 941, 'AUTHORIZED_SQL_SERVICE', {'source': 'test'})
    assert result['allowed'] is True
    assert len(result['payload_hash']) == 64
