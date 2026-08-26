from pathlib import Path
import sqlite3, sys, tempfile
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from engine.world.orchestrator import IntegrationOrchestrator
from engine.world.time_and_finance import WorldTickContext

BASE=ROOT/'data/database/game.db'
def clone(path):
 a=sqlite3.connect(BASE); b=sqlite3.connect(path); a.backup(b); a.close(); b.close()

def test_weekly_obligations_and_idempotent_posting():
 with tempfile.TemporaryDirectory() as d:
  path=Path(d)/'state.db'; clone(path); o=IntegrationOrchestrator(path)
  o.ensure_finance(1,1000); o.add_contract(1,'PLAYER_SALARY',100,'salario'); o.add_contract(1,'SPONSOR_PAYMENT',250,'master',contract_type='sponsor'); o.add_facility_obligation(1,'TRAINING',50,'manutencao')
  c=o.advance_week(seed=4)
  first=o.connection.execute('select cash from club_finances where club_id=1').fetchone()[0]
  count=o.connection.execute('select count(*) from financial_ledger').fetchone()[0]
  o.process_context(c)
  assert o.connection.execute('select count(*) from financial_ledger').fetchone()[0]==count
  assert o.connection.execute('select cash from club_finances where club_id=1').fetchone()[0]==first
  assert o.connection.execute('select current_week from logical_clock').fetchone()[0]==2
  o.close()

def test_expired_contract_does_not_pay():
 with tempfile.TemporaryDirectory() as d:
  path=Path(d)/'state.db'; clone(path); o=IntegrationOrchestrator(path)
  o.ensure_finance(1,0); o.add_contract(1,'SPONSOR_PAYMENT',999,'expirado',contract_type='sponsor',end_date='2020-01-01')
  o.advance_week(); assert o.connection.execute('select count(*) from financial_ledger').fetchone()[0]==0
  o.close()

def test_context_failure_rolls_back():
 with tempfile.TemporaryDirectory() as d:
  path=Path(d)/'state.db'; clone(path); o=IntegrationOrchestrator(path)
  c=o.clock.next_week_context()
  bad=WorldTickContext(c.tick_id,c.current_date,c.season,c.week,c.month)
  o.connection.execute('create trigger fail_audit before insert on orchestration_audit begin select raise(abort, "forced"); end')
  try: o.process_context(bad)
  except sqlite3.DatabaseError: pass
  assert o.connection.execute('select count(*) from financial_ledger').fetchone()[0]==0
  assert o.connection.execute('select current_week from logical_clock').fetchone()[0]==1
  o.close()


def test_process_context_can_join_external_transaction_without_commit():
 with tempfile.TemporaryDirectory() as d:
  path=Path(d)/'state.db'; clone(path); o=IntegrationOrchestrator(path)
  o.connection.execute('BEGIN')
  context=o.clock.next_week_context(seed=9)
  o.process_context(context, managed_transaction=False)
  assert o.connection.in_transaction
  o.connection.rollback()
  assert o.connection.execute('select current_week from logical_clock').fetchone()[0]==1
  o.close()
