import sqlite3
import pytest
from engine.core.domain_errors import DomainError
from engine.core.p1_scope_contract import ensure_p1_scope_registry,validate_p1_scope,audit_p1_scopes,persist_p1_scope,read_p1_scope_state

def db():
 c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row; ensure_p1_scope_registry(c); return c

def test_scope_bootstrap_and_audit():
 c=db(); assert validate_p1_scope(c,1171)['status']=='VALID'; assert audit_p1_scopes(c)['status']=='VALID'

def test_scope_state_is_idempotent():
 c=db(); persist_p1_scope(c,'scope-1',{'mode':'parallel'},3,actor='AUTHORIZED_SQL_SERVICE'); persist_p1_scope(c,'scope-1',{'mode':'national'},3,actor='AUTHORIZED_SQL_SERVICE'); rows=read_p1_scope_state(c,'scope-1'); assert len(rows)==1; assert rows[0]['payload_json']['mode']=='national'

def test_scope_mutation_requires_sql_actor():
 with pytest.raises(DomainError): persist_p1_scope(db(),'blocked',{},3,actor='FRONTEND')
