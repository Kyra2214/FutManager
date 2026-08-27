import sqlite3
from engine.staff.state_store import StaffStateStore

def test_ct_department_preview_approval_cash_and_audit():
    connection=sqlite3.connect(':memory:')
    connection.execute('CREATE TABLE times(time_id INTEGER PRIMARY KEY)')
    connection.execute('INSERT INTO times(time_id) VALUES(1)')
    store=StaffStateStore.__new__(StaffStateStore)
    store.connection=connection
    store.connection.row_factory=sqlite3.Row
    store.connection.execute('PRAGMA foreign_keys=ON')
    store.connection.executescript(__import__('engine.staff.state_store',fromlist=['SCHEMA']).SCHEMA)
    store.connection.commit()
    store.set_department(1,'medicina',1,1000,10,100,0.2)
    preview=store.preview_department_upgrade(1,'medicina',5000,2,10000)
    assert preview['cash_sufficient'] is True and preview['persisted'] is False
    approved=store.approve_department_upgrade(1,'medicina',2,5000,10000,'ct-up-1')
    assert approved['status']=='APPROVED'
    assert store.departments(1)[0]['level']==2
    assert store.department_audit(1)[0]['reference']=='ct-up-1'
    try:
        store.approve_department_upgrade(1,'medicina',3,5000,100,'ct-up-2')
    except ValueError as error:
        assert str(error)=='INSUFFICIENT_CASH'
    else:
        raise AssertionError('cash limit bypassed')
    store.close()
