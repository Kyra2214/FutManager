import sqlite3
import pytest
from engine.core.p1_country_contract import *

def test_country_contract_is_idempotent_and_protected():
 c=sqlite3.connect(':memory:'); c.row_factory=sqlite3.Row
 ensure_p1_country_registry(c); ensure_p1_country_registry(c)
 assert len(read_p1_countries(c))==10
 assert all(validate_p1_country(c,i)['status']=='VALID' for i in ITEM_IDS)
 with pytest.raises(Exception): persist_p1_country(c,'br',29,'Brasil',{},actor='FRONTEND')
 row=persist_p1_country(c,'br',29,'Brasil',{'clubs':80},actor='AUTHORIZED_SQL_SERVICE')
 assert row['payload_hash']
 assert read_p1_country_state(c,'br')[0]['country_name']=='Brasil'
 assert protect_p1_country_mutation(c,1255,'AUTHORIZED_SQL_SERVICE',{'status':'ACTIVE'})['allowed'] is True
 with pytest.raises(Exception): protect_p1_country_mutation(c,1255,'FRONTEND',{})
 assert audit_p1_countries(c)['status']=='VALID'
