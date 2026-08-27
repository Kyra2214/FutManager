import sqlite3
from engine.manager.career import ManagerService

def test_snapshot_hash_compare_selective_restore_retention_and_audit():
    c=sqlite3.connect(':memory:')
    c.execute('CREATE TABLE times(time_id INTEGER PRIMARY KEY)'); c.execute('INSERT INTO times VALUES(1)')
    service=ManagerService(c)
    manager=service.create_manager('Manager','BR',30)
    career=service.create_career(manager,'Carreira',1,2027)
    snapshot=service.snapshot(career)
    digest=service.snapshot_hash(snapshot)
    compared=service.compare_snapshots(snapshot,snapshot)
    assert len(digest)==64 and compared['identical'] is True
    restored=service.restore_selective(manager,snapshot,['current_club_id'])
    assert restored['restored'] is True and service.recovery_audit(career)[0]['action']=='RESTORE_SELECTIVE'
    assert service.retain_snapshots(career,1)==0
