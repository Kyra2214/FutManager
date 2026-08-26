from pathlib import Path
import sqlite3,sys,tempfile
from datetime import date
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.world.simulation import WorldSimulationService,SimulationLevel
from engine.manager.career import ManagerService
from engine.competitions.match_engine import CompetitionService
BASE=ROOT/'data/database/game.db'
def clone(p):
 a=sqlite3.connect(BASE);b=sqlite3.connect(p);a.backup(b);a.close();b.close()

def test_world_simulation_batch_and_idempotency():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'s.db';clone(p);c=CompetitionService(p);season=c.create_season(2026);comp=c.create_competition('Mundo',season,[1,2,3]);c.generate_fixtures(comp);c.close();s=WorldSimulationService(p);a=s.simulate_batch('tick-1',SimulationLevel.FAST,batch_size=2,seed=7);assert a['processed']==2;b=s.simulate_batch('tick-1',SimulationLevel.FAST,batch_size=2,seed=7);assert b['status']=='ALREADY_PROCESSED';assert s.connection.execute('select count(*) from simulation_audit').fetchone()[0]==2;s.close()

def test_manager_career_contract_objective_inbox_and_resign():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'s.db';clone(p);m=ManagerService(p);mid=m.create_manager('Manager A','BR',40);cid=m.create_career(mid,'Carreira 1',1,1);m.sign(mid,1,'2026-01-01','2027-01-01',1000,'TOP4');oid=m.objective(cid,'QUALIFY_CONTINENTAL',90);m.inbox(mid,'MATCH','Partida importante','Jogo amanhã','match:1');assert m.load(mid)['current_club_id']==1;assert m.connection.execute('select count(*) from manager_objectives where objective_id=?',(oid,)).fetchone()[0]==1;m.resign(mid,'teste');assert m.load(mid)['status']=='RESIGNED';m.close()

def test_manager_starts_a_single_career_with_club_or_selection():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'club.db';clone(p);m=ManagerService(p);started=m.start_career('Ana','BR',31,'Carreira Ana','club',1);assert started['current_club_id']==1;assert m.load(started['manager_id'])['current_club_id']==1;assert m.connection.execute('select count(*) from manager_selection_assignments').fetchone()[0]==0;m.close()
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'selection.db';clone(p);m=ManagerService(p);started=m.start_career('Bia','AR',33,'Carreira Bia','selection',1);assert started['current_club_id'] is None;assert m.connection.execute('select selection_id from manager_selection_assignments where career_id=?',(started['career_id'],)).fetchone()[0]==1;m.close()


def test_world_simulation_cooperative_cancellation():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'cancel.db';clone(p);c=CompetitionService(p);season=c.create_season(2026);comp=c.create_competition('Mundo Cancelável',season,[1,2,3]);c.generate_fixtures(comp);c.close()
  s=WorldSimulationService(p);result=s.simulate_batch('tick-cancel',SimulationLevel.FAST,batch_size=2,seed=11,cancel_check=lambda: True)
  assert result == {'status':'CANCELLED','processed':0}
  row=s.connection.execute("select status,processed from simulation_ticks where simulation_tick_id='tick-cancel'").fetchone()
  assert (row['status'],row['processed'])==('CANCELLED',0)
  s.close()


def test_match_can_be_postponed_and_rescheduled_in_temporary_state():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'schedule.db';clone(p);c=CompetitionService(p);season=c.create_season(2099);comp=c.create_competition('Teste remarcacao',season,[1,2]);match_id=c.generate_fixtures(comp)[0];c.postpone(match_id,'2099-02-01');row=c.connection.execute('select status,match_date from matches where match_id=?',(match_id,)).fetchone();assert (row['status'],row['match_date'])==('POSTPONED','2099-02-01');c.reschedule(match_id,'2099-02-08');row=c.connection.execute('select status,match_date from matches where match_id=?',(match_id,)).fetchone();assert (row['status'],row['match_date'])==('SCHEDULED','2099-02-08');c.close()
