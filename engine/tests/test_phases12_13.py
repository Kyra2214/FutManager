from pathlib import Path
import sqlite3,sys,tempfile
from datetime import date
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.economy.world_economy import EconomyService,FinancialHealth,OwnershipType
from engine.ai.club_ai import ClubAI,Personality
from engine.world.time_and_finance import WorldTickContext
BASE=ROOT/'data/database/game.db'
def clone(p):
 a=sqlite3.connect(BASE);b=sqlite3.connect(p);a.backup(b);a.close();b.close()

def test_economy_obligation_debt_health_and_investment():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'s.db';clone(p);e=EconomyService(p);e.ensure_club(1,1000,500); assert e.budget(1).cash==1000; oid=e.obligation(1,'SALARY',200,'2026-01-01'); ctx=WorldTickContext('econ1',date(2026,1,2),2026,1,1); assert e.settle_due(ctx)==[(oid,'PAID')]; assert e.connection.execute('select cash from club_economic_state where club_id=1').fetchone()[0]==800; e.add_debt(1,100); e.invest(1,'Investor',500,51,ctx); e.buy_control(1,'Investor',OwnershipType.SAF.value,51,ctx); assert e.connection.execute("select count(*) from investments where club_id=1").fetchone()[0]==1; assert e.connection.execute("select count(*) from club_ownership where club_id=1 and status='ACTIVE'").fetchone()[0]==1; e.close()

def test_overdue_and_bankruptcy_history():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'s.db';clone(p);e=EconomyService(p);e.ensure_club(2,0,0); oid=e.obligation(2,'MAINTENANCE',100,'2026-01-01'); status=e.declare_bankruptcy(2,WorldTickContext('x',date(2026,1,2),2026,1,1)); assert status=='NORMAL' or status=='RECOVERY'; e.settle_due(WorldTickContext('y',date(2026,1,2),2026,1,2)); assert e.connection.execute('select status from financial_obligations where obligation_id=?',(oid,)).fetchone()[0]=='OVERDUE'; e.close()

def test_club_ai_reads_state_and_audits_deterministic_decision():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'s.db';clone(p);e=EconomyService(p);e.ensure_club(1,10000,5000);e.close();a=ClubAI(p);a.set_profile(1,Personality.FINANCIAL,seed=42);a.add_objective(1,'IMPROVE_FINANCES',90);dgn=a.diagnose(1); assert dgn.cash==10000; assert a.propose_training(1)=='GENERAL'; assert len(a.history(1))==1; a.close()
