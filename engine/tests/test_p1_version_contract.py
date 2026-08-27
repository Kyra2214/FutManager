import sqlite3

import pytest

from engine.core.domain_errors import DomainError
from engine.core.p1_version_contract import audit_p1_versions, ensure_p1_version_registry, protect_p1_version_mutation, read_p1_versions, validate_p1_version


def test_p1_version_registry_is_idempotent_and_semver_valid():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    ensure_p1_version_registry(connection)
    ensure_p1_version_registry(connection)
    assert len(read_p1_versions(connection)) == 10
    assert validate_p1_version(connection, 1071)['status'] == 'VALID'
    assert validate_p1_version(connection, 1080)['status'] == 'VALID'
    assert audit_p1_versions(connection)['status'] == 'VALID'


def test_p1_version_mutation_requires_sql_service():
    connection = sqlite3.connect(':memory:')
    connection.row_factory = sqlite3.Row
    ensure_p1_version_registry(connection)
    with pytest.raises(DomainError, match='P0_MUTATION_AUTHORIZATION_REQUIRED'):
        protect_p1_version_mutation(connection, 1071, 'FRONTEND', {})
    assert protect_p1_version_mutation(connection, 1071, 'AUTHORIZED_SQL_SERVICE', {})['allowed']
