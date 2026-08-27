import sqlite3
import pytest
from engine.core.domain_errors import DomainError
from engine.core.p1_invite_contract import ensure_p1_invite_registry, validate_p1_invite, audit_p1_invites, persist_p1_invite, read_p1_invite_state

def db():
 c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row; ensure_p1_invite_registry(c); return c

def test_invite_contract_bootstrap_audit():
 c=db(); assert validate_p1_invite(c,1181)['status']=='VALID'; assert audit_p1_invites(c)['status']=='VALID'

def test_invite_upsert_and_read():
 c=db(); persist_p1_invite(c,'i1','PENDING',{'message':'ok'},1,2,3,'AUTHORIZED_SQL_SERVICE'); persist_p1_invite(c,'i1','ACCEPTED',{'message':'ok'},1,2,3,'AUTHORIZED_SQL_SERVICE'); assert read_p1_invite_state(c,'i1')[0]['status']=='ACCEPTED'

def test_invite_mutation_requires_sql_actor():
 with pytest.raises(DomainError): persist_p1_invite(db(),'blocked','PENDING',{},actor='FRONTEND')
