import sqlite3
import pytest
from engine.core.domain_errors import DomainError
from engine.core.p1_mfa_contract import ensure_p1_mfa_registry,validate_p1_mfa,audit_p1_mfas,persist_p1_mfa,read_p1_mfa_state

def db():
 c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row; ensure_p1_mfa_registry(c); return c

def test_mfa_contract_bootstrap():
 c=db(); assert validate_p1_mfa(c,1201)['status']=='VALID'; assert audit_p1_mfas(c)['status']=='VALID'

def test_mfa_upsert():
 c=db(); persist_p1_mfa(c,'m1',{'enabled':True},3,7,'TOTP','PENDING','AUTHORIZED_SQL_SERVICE'); persist_p1_mfa(c,'m1',{'enabled':True},3,7,'TOTP','ENABLED','AUTHORIZED_SQL_SERVICE'); assert read_p1_mfa_state(c,'m1')[0]['status']=='ENABLED'

def test_mfa_requires_sql_actor():
 with pytest.raises(DomainError): persist_p1_mfa(db(),'blocked',{},3,7,actor='FRONTEND')
