from pathlib import Path
import sqlite3, sys, tempfile
from datetime import date
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from engine.staff.state_store import StaffStateStore
from engine.staff.domain import StaffRole
from engine.transfers.market import TransferMarketService, OfferStatus
from engine.scouting.service import ScoutService, MissionStatus
from engine.world.time_and_finance import WorldTickContext
BASE=ROOT/'data/database/game.db'
def clone(path):
 a=sqlite3.connect(BASE); b=sqlite3.connect(path); a.backup(b); a.close(); b.close()

def test_transfer_atomic_finance_history_and_idempotency():
 with tempfile.TemporaryDirectory() as d:
  path=Path(d)/'state.db'; clone(path); staff=StaffStateStore(path); staff.close(); m=TransferMarketService(path)
  m.connection.execute("insert into club_finances(club_id,cash,updated_at) values(1,1000000,'2026-01-01'),(2,0,'2026-01-01')")
  m.connection.execute("insert into player_market_state(player_id,club_id,status,market_value,asking_price) values(77,2,'ACTIVE',300000,400000)"); m.connection.commit()
  w=m.open_window(2026,1,'2026-01-01','2026-02-01'); o=m.create_offer(77,1,2,300000,w,400000); m.counter(o,350000); assert m.temperature(o).value in ('NEUTRAL','WARM','HOT'); m.accept(o)
  c=WorldTickContext('t1',date(2026,1,8),2026,1,1)
  m.complete(o,c); assert m.connection.execute('select cash from club_finances where club_id=1').fetchone()[0]==650000
  assert m.connection.execute('select club_id from player_market_state where player_id=77').fetchone()[0]==1
  assert m.connection.execute('select count(*) from transfer_history').fetchone()[0]==1
  try: m.complete(o,c)
  except ValueError as e: assert str(e)=='ALREADY_COMPLETED'
  else: raise AssertionError('transferência duplicada aceita')
  assert m.connection.execute('select count(*) from transfer_history').fetchone()[0]==1; m.close()

def test_scout_mission_filters_seed_and_report():
 with tempfile.TemporaryDirectory() as d:
  path=Path(d)/'state.db'; clone(path); s=StaffStateStore(path); sid=s.create_staff('Scout A',StaffRole.SCOUT,35,club_id=1,seed=1); s.close(); sc=ScoutService(path)
  mid=sc.create_mission(1,sid,'2026-01-01',3,position_code=4,min_age=16,max_age=99,seed=42); sc.start(mid); rows=sc.complete(mid,'2026-04-01',limit=5)
  assert sc._mission(mid)['status']==MissionStatus.COMPLETED.value
  assert len(rows)<=5 and all(r['position_code']==4 and 16<=r['age']<=99 for r in rows)
  assert sc.connection.execute('select count(*) from scout_reports where mission_id=?',(mid,)).fetchone()[0]==1; sc.close()

def test_invalid_scout_duration_and_rollback():
 with tempfile.TemporaryDirectory() as d:
  path=Path(d)/'state.db'; clone(path); s=StaffStateStore(path); sid=s.create_staff('Scout A',StaffRole.SCOUT,35,club_id=1,seed=1); s.close(); sc=ScoutService(path)
  try: sc.create_mission(1,sid,'2026-01-01',5)
  except ValueError as e: assert str(e)=='INVALID_DURATION'
  else: raise AssertionError('duração inválida aceita')
  sc.close()


def test_scout_seed_expiration_reports_and_missing_fields(tmp_path):
 with tempfile.TemporaryDirectory() as d:
  path=Path(d)/'state.db'; clone(path); s=StaffStateStore(path); sid=s.create_staff('Scout B',StaffRole.SCOUT,35,club_id=1,seed=2); s.close(); sc=ScoutService(path)
  first=sc.create_mission(1,sid,'2026-01-01',1,seed=91); second=sc.create_mission(1,sid,'2026-01-01',1,seed=91)
  sc.start(first); sc.start(second)
  try: sc.complete(first,'2026-01-15')
  except ValueError as error: assert str(error)=='MISSION_NOT_DUE'
  else: raise AssertionError('missão expirada foi concluída antes do prazo')
  a=[dict(row) for row in sc.complete(first,'2026-02-01')]; b=[dict(row) for row in sc.complete(second,'2026-02-01')]
  assert [row['player_id'] for row in a] == [row['player_id'] for row in b]
  assert sc.connection.execute('select count(*) from scout_reports where mission_id in (?,?)',(first,second)).fetchone()[0] == 2
  assert all('atributos avançados não disponíveis' in row['observations'] for row in a)
  sc.close()
