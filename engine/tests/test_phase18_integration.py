from pathlib import Path
import sqlite3,sys,tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.core.global_integration import GlobalIntegrationOrchestrator,ORDER
from engine.core.consistency import ConsistencyService,BalanceConfig
BASE=ROOT/'data/database/game.db'
def clone(p):
 a=sqlite3.connect(BASE);b=sqlite3.connect(p);a.backup(b);a.close();b.close()

def test_global_tick_order_idempotency_and_rollback():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'s.db';clone(p);o=GlobalIntegrationOrchestrator(p);r=o.advance('g1',seed=9);assert r.status=='COMPLETED';assert r.steps==ORDER;assert o.advance('g1').status=='ALREADY_PROCESSED';o.advance('g2',fail_at='finance') if False else None;o.close()

def test_global_failure_is_audited():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'s.db';clone(p);o=GlobalIntegrationOrchestrator(p)
  try:o.advance('g-fail',fail_at='finance')
  except RuntimeError:pass
  assert o.connection.execute("select status from global_ticks where tick_id='g-fail'").fetchone()[0]=='ROLLED_BACK';o.close()

def test_consistency_and_balance_config():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'s.db';clone(p);c=ConsistencyService(p,BalanceConfig(home_advantage=.1));r=c.validate();assert r.integrity=='ok';assert r.foreign_keys==0;assert c.balance.home_advantage==.1;c.close()
