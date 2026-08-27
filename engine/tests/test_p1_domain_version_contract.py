import sqlite3
from engine.core.p1_domain_version_contract import audit_p1_domain_versions, ensure_p1_domain_version_registry, read_p1_domain_versions, validate_p1_domain_version

def test_domain_version_registry_is_idempotent_and_valid():
    c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row
    ensure_p1_domain_version_registry(c); ensure_p1_domain_version_registry(c)
    assert len(read_p1_domain_versions(c)) == 10
    assert validate_p1_domain_version(c,1091)['status'] == 'VALID'
    assert validate_p1_domain_version(c,1100)['status'] == 'VALID'
    assert audit_p1_domain_versions(c)['status'] == 'VALID'
