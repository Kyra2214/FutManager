import sqlite3
import pytest
from engine.core.domain_errors import DomainError
from engine.core.p1_consent_contract import ensure_p1_consent_registry,validate_p1_consent,audit_p1_consents,persist_p1_consent,read_p1_consent_state

def db():
 c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row; ensure_p1_consent_registry(c); return c

def test_consent_contract_bootstrap():
 c=db(); assert validate_p1_consent(c,1211)['status']=='VALID'; assert audit_p1_consents(c)['status']=='VALID'

def test_consent_upsert():
 c=db(); persist_p1_consent(c,'c1',{'version':1},3,7,'CAREER_DATA','PENDING','AUTHORIZED_SQL_SERVICE'); persist_p1_consent(c,'c1',{'version':1},3,7,'CAREER_DATA','GRANTED','AUTHORIZED_SQL_SERVICE'); assert read_p1_consent_state(c,'c1')[0]['status']=='GRANTED'

def test_consent_requires_sql_actor():
 with pytest.raises(DomainError): persist_p1_consent(db(),'blocked',{},3,7,actor='FRONTEND')
