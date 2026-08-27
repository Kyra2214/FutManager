import sqlite3
import pytest
from engine.core.domain_errors import DomainError
from engine.core.p1_migration_contract import audit_p1_migrations, ensure_p1_migration_registry, protect_p1_migration_mutation, read_p1_migrations, validate_p1_migration

def test_migration_registry_is_idempotent():
    c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row
    ensure_p1_migration_registry(c); ensure_p1_migration_registry(c)
    assert len(read_p1_migrations(c)) == 10
    assert validate_p1_migration(c,1081)['status'] == 'VALID'
    assert validate_p1_migration(c,1090)['status'] == 'VALID'
    assert audit_p1_migrations(c)['status'] == 'VALID'

def test_migration_mutation_requires_sql_service():
    c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row
    ensure_p1_migration_registry(c)
    with pytest.raises(DomainError): protect_p1_migration_mutation(c,1081,'FRONTEND',{})
    assert protect_p1_migration_mutation(c,1081,'AUTHORIZED_SQL_SERVICE',{})['allowed']
