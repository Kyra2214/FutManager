from pathlib import Path
import sqlite3, sys, tempfile
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from engine.staff.state_store import StaffStateStore
from engine.staff.domain import StaffRole, StaffStatus, StaffMember
from engine.teams.club_strength import ClubStrengthService

BASE=ROOT/'data/database/game.db'
def clone(path):
 a=sqlite3.connect(BASE); b=sqlite3.connect(path); a.backup(b); a.close(); b.close()

def test_staff_creation_experience_transfer_retirement_and_department():
 with tempfile.TemporaryDirectory() as d:
  path=Path(d)/'state.db'; clone(path); s=StaffStateStore(path)
  sid=s.create_staff('Treinador Teste',StaffRole.MANAGER,38,club_id=1,seed=10)
  row=s.connection.execute('select * from staff_members where staff_id=?',(sid,)).fetchone()
  assert 30<=row['potential']<=99
  s.add_experience(sid,30,'boa campanha')
  assert s.connection.execute('select level from staff_members where staff_id=?',(sid,)).fetchone()[0]>=3
  s.transfer(sid,2); assert s.connection.execute('select club_id from staff_members where staff_id=?',(sid,)).fetchone()[0]==2
  s.retire(sid); row=s.connection.execute('select status,club_id from staff_members where staff_id=?',(sid,)).fetchone(); assert row['status']=='aposentado' and row['club_id'] is None
  s.set_department(1,'treinamento',level=4,efficiency=.7)
  assert s.connection.execute('select level from club_departments where club_id=1').fetchone()[0]==4
  s.close()

def test_staff_seed_and_strength_components():
 a=StaffStateStore.__name__; assert a=='StaffStateStore'
 x=StaffMember(None,'A',StaffRole.ASSISTANT,35,experience=50,reputation=50,level=5,potential=80)
 c=ClubStrengthService().calculate([80,90],[x],[60,70])
 assert c.players==85 and c.staff>0 and c.infrastructure==65 and c.total>c.players


def test_staff_and_department_read_models_are_sql_canonical(tmp_path):
    path=tmp_path/'staff-read.db'; clone(path); store=StaffStateStore(path)
    manager=store.create_staff('Treinador',StaffRole.MANAGER,40,club_id=1,seed=1)
    store.create_staff('Auxiliar',StaffRole.ASSISTANT,35,club_id=1,seed=2)
    store.create_staff('Livre',StaffRole.SCOUT,30,club_id=None,seed=3)
    store.set_department(1,'medicina',level=4,capacity=12,efficiency=.8)
    summary=store.staff_summary(1)
    assert summary['total'] == 2 and summary['by_role'][StaffRole.MANAGER.value] == 1
    assert len(store.active_staff(1,StaffRole.MANAGER)) == 1
    assert store.active_staff(1,StaffRole.SCOUT) == []
    assert store.departments(1)[0]['department'] == 'medicina'
    assert store.staff_history(1,manager)[0]['event_type'] == 'STAFF_CREATED'
    store.close()


def test_staff_domain_effects_capacity_bonus_and_specialists(tmp_path):
    path=tmp_path/'staff_domain.db'
    con=sqlite3.connect(path)
    con.execute('CREATE TABLE times(time_id INTEGER PRIMARY KEY)')
    con.execute('INSERT INTO times VALUES (1)')
    con.commit(); con.close()
    store=StaffStateStore(path)
    doctor=store.create_staff('Dra. Teste',StaffRole.DOCTOR,40,1,seed=1)
    assistant=store.create_staff('Auxiliar Tático',StaffRole.ASSISTANT,35,1,seed=2)
    store.connection.execute("UPDATE staff_members SET level=8,specialization='medicina esportiva' WHERE staff_id=?",(doctor,))
    store.connection.execute("UPDATE staff_members SET level=6,specialization='transição' WHERE staff_id=?",(assistant,))
    store.connection.execute("INSERT INTO club_departments VALUES (1,'medicina',2,0,3,0,0.2)")
    store.connection.commit()
    effects=store.domain_effects(1)
    assert effects['medico']['effect']=='HEALTH' and effects['medico']['bonus']==0.2
    assert store.department_capacity(1)[0]['vacancies']==2
    assert store.commission_bonus(1)['bonus']==0.35
    assert store.specialists(1,'medico')[0]['specialization']=='medicina esportiva'
    store.close()
