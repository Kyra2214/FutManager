import sqlite3
import pytest
from engine.core.domain_errors import DomainError
from engine.core.p1_revocation_contract import ensure_p1_revocation_registry,validate_p1_revocation,audit_p1_revocations,persist_p1_revocation,read_p1_revocation_state

def db():
 c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row; ensure_p1_revocation_registry(c); return c

def test_revocation_contract_bootstrap():
 c=db(); assert validate_p1_revocation(c,1191)['status']=='VALID'; assert audit_p1_revocations(c)['status']=='VALID'

def test_revocation_upsert():
 c=db(); persist_p1_revocation(c,'r1',{'source':'invite'},3,7,'user request','ACTIVE','AUTHORIZED_SQL_SERVICE'); persist_p1_revocation(c,'r1',{'source':'invite'},3,7,'user request','REVOKED','AUTHORIZED_SQL_SERVICE'); assert read_p1_revocation_state(c,'r1')[0]['status']=='REVOKED'

def test_revocation_requires_sql_actor():
 with pytest.raises(DomainError): persist_p1_revocation(db(),'blocked',{},3,7,actor='FRONTEND')
