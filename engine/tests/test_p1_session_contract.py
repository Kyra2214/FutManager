from __future__ import annotations

import sqlite3
import pytest
from engine.core.domain_errors import DomainError
from engine.core.p1_session_contract import ensure_p1_session_registry, validate_p1_session, audit_p1_sessions, persist_p1_session, read_p1_session_state


def db():
    c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row; ensure_p1_session_registry(c); return c


def test_session_contract_bootstrap_and_audit():
    c=db(); assert validate_p1_session(c,1151)['status']=='VALID'; assert audit_p1_sessions(c)['status']=='VALID'


def test_session_state_is_upserted_and_readable():
    c=db(); first=persist_p1_session(c,'s1','ACTIVE',{'nonce':'n'},7,3,'AUTHORIZED_SQL_SERVICE'); second=persist_p1_session(c,'s1','REVOKED',{'nonce':'n'},7,3,'AUTHORIZED_SQL_SERVICE'); assert first['session_key']==second['session_key']; assert read_p1_session_state(c,'s1')[0]['status']=='REVOKED'


def test_session_mutation_requires_sql_actor():
    with pytest.raises(DomainError): persist_p1_session(db(),'blocked','ACTIVE',{},actor='FRONTEND')
