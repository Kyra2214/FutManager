import sqlite3
from engine.core.p1_timeout_contract import audit_p1_timeouts, ensure_p1_timeout_registry, read_p1_timeouts, validate_p1_timeout

def test_timeout_registry_is_idempotent_and_valid():
    c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row
    ensure_p1_timeout_registry(c); ensure_p1_timeout_registry(c)
    assert len(read_p1_timeouts(c)) == 10
    assert validate_p1_timeout(c,1101)['status'] == 'VALID'
    assert validate_p1_timeout(c,1110)['status'] == 'VALID'
    assert audit_p1_timeouts(c)['status'] == 'VALID'
