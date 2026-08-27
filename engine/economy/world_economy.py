from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
import json
import sqlite3
from engine.world.time_and_finance import FinanceLedger, WorldTickContext, LogicalClock

from engine.core.state_store import assert_mutable_state_path
SCHEMA='''
CREATE TABLE IF NOT EXISTS club_economic_state(club_id INTEGER PRIMARY KEY,cash INTEGER NOT NULL DEFAULT 0,budget INTEGER NOT NULL DEFAULT 0,revenue_accumulated INTEGER NOT NULL DEFAULT 0,expense_accumulated INTEGER NOT NULL DEFAULT 0,debt INTEGER NOT NULL DEFAULT 0,obligations INTEGER NOT NULL DEFAULT 0,payroll INTEGER NOT NULL DEFAULT 0,financial_status TEXT NOT NULL DEFAULT 'HEALTHY',updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS financial_obligations(obligation_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,type TEXT NOT NULL,amount INTEGER NOT NULL,due_date TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'PENDING',origin TEXT,reference TEXT,paid_at TEXT);
CREATE TABLE IF NOT EXISTS club_debts(debt_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,principal INTEGER NOT NULL,balance INTEGER NOT NULL,interest REAL NOT NULL DEFAULT 0,due_date TEXT,status TEXT NOT NULL DEFAULT 'ACTIVE',creditor TEXT,origin TEXT);
CREATE TABLE IF NOT EXISTS club_financial_history(history_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,event_type TEXT NOT NULL,event_date TEXT NOT NULL,payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS club_ownership(ownership_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,owner_type TEXT NOT NULL,owner_name TEXT NOT NULL,participation REAL NOT NULL,start_date TEXT NOT NULL,end_date TEXT,status TEXT NOT NULL DEFAULT 'ACTIVE');
CREATE TABLE IF NOT EXISTS investments(investment_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,investor TEXT NOT NULL,value INTEGER NOT NULL,percentage REAL NOT NULL,investment_date TEXT NOT NULL,type TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'COMPLETED');
CREATE TABLE IF NOT EXISTS financial_alerts(alert_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,alert_type TEXT NOT NULL,status TEXT NOT NULL,threshold INTEGER NOT NULL,cash INTEGER NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,UNIQUE(club_id,alert_type));
CREATE TABLE IF NOT EXISTS economy_season_audits(audit_id INTEGER PRIMARY KEY AUTOINCREMENT,season INTEGER NOT NULL UNIQUE,currency TEXT NOT NULL,payload TEXT NOT NULL,created_at TEXT NOT NULL);
'''
class FinancialHealth(StrEnum): HEALTHY='HEALTHY'; STABLE='STABLE'; WARNING='WARNING'; CRITICAL='CRITICAL'; INSOLVENT='INSOLVENT'
class ObligationStatus(StrEnum): PENDING='PENDING'; PAID='PAID'; OVERDUE='OVERDUE'; CANCELLED='CANCELLED'
class BankruptcyStatus(StrEnum): NORMAL='NORMAL'; WARNING='WARNING'; RECOVERY='RECOVERY'; INSOLVENT='INSOLVENT'; BANKRUPT='BANKRUPT'
class OwnershipType(StrEnum): MEMBERS='MEMBERS'; PRIVATE='PRIVATE'; CORPORATE='CORPORATE'; SAF='SAF'; OTHER='OTHER'
@dataclass(frozen=True)
class Budget: cash:int; transfer_budget:int; payroll_budget:int; projected_expenses:int; projected_revenue:int; safety_margin:int
class EconomyService:
 def __init__(self,db):
  assert_mutable_state_path(db) if not isinstance(db,sqlite3.Connection) else None;self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db; self.connection.row_factory=sqlite3.Row; self.connection.execute('PRAGMA foreign_keys=ON'); self.connection.executescript(SCHEMA); self.connection.commit(); LogicalClock(self.connection); self.ledger=FinanceLedger(self.connection)
 def ensure_club(self,club_id,cash=0,budget=0):
  self.connection.execute('insert or ignore into club_economic_state(club_id,cash,budget,updated_at) values(?,?,?,?)',(club_id,cash,budget,date.today().isoformat())); self.connection.commit()
 def budget(self,club_id,projected_revenue=0,projected_expenses=0,safety_ratio=.15):
  r=self.connection.execute('select * from club_economic_state where club_id=?',(club_id,)).fetchone()
  if not r: raise KeyError(club_id)
  margin=int(max(0,r['cash']+projected_revenue-projected_expenses)); return Budget(r['cash'],int(margin*(1-safety_ratio)),max(0,r['budget']-projected_expenses),projected_expenses,projected_revenue,int(margin*safety_ratio))
 def preview_expense(self, club_id, amount, category='OTHER'):
  if int(amount) < 0: raise ValueError('EXPENSE_AMOUNT_INVALID')
  row=self.connection.execute('select cash from club_economic_state where club_id=?',(club_id,)).fetchone()
  if not row: raise KeyError(club_id)
  return {'club_id': club_id, 'category': str(category), 'amount': int(amount), 'cash_before': int(row['cash']), 'cash_after': int(row['cash'])-int(amount), 'cash_sufficient': int(row['cash'])>=int(amount), 'persisted': False, 'formula_version': 'expense-preview-v1'}

 def post_match_projection(self, club_id, matchday_revenue=0, matchday_expense=0):
  row=self.connection.execute('select cash from club_economic_state where club_id=?',(club_id,)).fetchone()
  if not row: raise KeyError(club_id)
  return {'club_id': club_id, 'matchday_revenue': int(matchday_revenue), 'matchday_expense': int(matchday_expense), 'cash_before': int(row['cash']), 'cash_after_match': int(row['cash'])+int(matchday_revenue)-int(matchday_expense), 'persisted': False, 'formula_version': 'post-match-preview-v1'}

 def projection_39_weeks(self, club_id, weekly_revenue=0, weekly_expenses=0):
  row = self.connection.execute('select cash from club_economic_state where club_id=?', (club_id,)).fetchone()
  if not row: raise KeyError(club_id)
  return {'club_id': club_id, 'currency': self.ledger.CURRENCY, 'weeks': 39, 'weekly_revenue': int(weekly_revenue), 'weekly_expenses': int(weekly_expenses), 'starting_cash': int(row['cash']), 'ending_cash': int(row['cash'] + 39 * (weekly_revenue - weekly_expenses)), 'reserve_weeks': 39}

 def low_balance_alert(self, club_id, threshold_weeks=4):
  row = self.connection.execute('select cash,payroll from club_economic_state where club_id=?', (club_id,)).fetchone()
  if not row: raise KeyError(club_id)
  threshold = max(0, int(row['payroll']) * int(threshold_weeks))
  status = 'LOW_BALANCE' if int(row['cash']) < threshold else 'OK'
  now = date.today().isoformat()
  self.connection.execute('INSERT INTO financial_alerts(club_id,alert_type,status,threshold,cash,created_at,updated_at) VALUES(?,?,?,?,?,?,?) ON CONFLICT(club_id,alert_type) DO UPDATE SET status=excluded.status,threshold=excluded.threshold,cash=excluded.cash,updated_at=excluded.updated_at', (club_id, 'LOW_BALANCE', status, threshold, int(row['cash']), now, now))
  self.connection.commit()
  return {'club_id': club_id, 'currency': self.ledger.CURRENCY, 'threshold': threshold, 'cash': int(row['cash']), 'status': status, 'persisted': True}

 def controlled_deficit(self, club_id, amount, context: WorldTickContext, origin='controlled_deficit'):
  if amount <= 0: raise ValueError('DEFICIT_AMOUNT_INVALID')
  self.ensure_club(club_id)
  reference = f'{context.season}:{context.week}:{club_id}:{origin}'
  posted = self.ledger.post(context, club_id, 'EXPENSE', 'OTHER', -int(amount), origin, reference, 'Déficit controlado')
  if posted:
   self.connection.execute('update club_economic_state set cash=cash-?,debt=debt+?,expense_accumulated=expense_accumulated+?,updated_at=? where club_id=?', (amount, amount, amount, context.current_date.isoformat(), club_id))
  self.connection.commit()
  return {'club_id': club_id, 'amount': int(amount), 'posted': posted, 'status': 'CONTROLLED'}

 def report_revenue(self, club_id, season=None):
  return self.ledger.report_club(club_id, season)['income']

 def report_expense(self, club_id, season=None):
  return self.ledger.report_club(club_id, season)['expense']

 def report_world(self, season=None):
  return self.ledger.world_report(season)

 def audit_season(self, season):
  report = self.ledger.season_audit(season)
  now = date.today().isoformat()
  self.connection.execute('INSERT INTO economy_season_audits(season,currency,payload,created_at) VALUES(?,?,?,?) ON CONFLICT(season) DO UPDATE SET currency=excluded.currency,payload=excluded.payload,created_at=excluded.created_at', (season, self.ledger.CURRENCY, json.dumps(report, sort_keys=True), now))
  self.connection.commit()
  return {**report, 'persisted': True}

 def obligation(self,club_id,type_,amount,due_date,origin=None,reference=None):
  cur=self.connection.execute('insert into financial_obligations(club_id,type,amount,due_date,origin,reference) values(?,?,?,?,?,?)',(club_id,type_,amount,due_date,origin,reference)); self.connection.commit(); return int(cur.lastrowid)
 def settle_due(self,context:WorldTickContext):
  rows=self.connection.execute("select * from financial_obligations where status='PENDING' and due_date<=?",(context.current_date.isoformat(),)).fetchall(); done=[]
  for r in rows:
   state=self.connection.execute('select cash from club_economic_state where club_id=?',(r['club_id'],)).fetchone()
   if not state or state['cash']<r['amount']:
    self.connection.execute("update financial_obligations set status='OVERDUE' where obligation_id=?",(r['obligation_id'],)); done.append((r['obligation_id'],'OVERDUE')); continue
   self.ledger.post(context,r['club_id'],'EXPENSE',r['type'],-r['amount'],'obligation',str(r['obligation_id']),r['type']); self.connection.execute('update club_economic_state set cash=cash-?,expense_accumulated=expense_accumulated+?,updated_at=? where club_id=?',(r['amount'],r['amount'],context.current_date.isoformat(),r['club_id'])); self.connection.execute("update financial_obligations set status='PAID',paid_at=? where obligation_id=?",(context.current_date.isoformat(),r['obligation_id'])); done.append((r['obligation_id'],'PAID'))
  self.connection.commit(); return done
 def health(self,club_id):
  r=self.connection.execute('select * from club_economic_state where club_id=?',(club_id,)).fetchone();
  if not r: raise KeyError(club_id)
  overdue=self.connection.execute("select coalesce(sum(amount),0) from financial_obligations where club_id=? and status='OVERDUE'",(club_id,)).fetchone()[0]
  if r['debt']>max(1,r['cash']*3) or overdue>max(1,r['cash']): return FinancialHealth.INSOLVENT
  if overdue>0 or r['cash']<0: return FinancialHealth.CRITICAL
  if r['debt']>max(1,r['cash']*2): return FinancialHealth.WARNING
  if r['cash']<r['payroll']: return FinancialHealth.STABLE
  return FinancialHealth.HEALTHY
 def add_debt(self,club_id,principal,interest=0,due_date=None,creditor='unknown',origin='manual'):
  self.ensure_club(club_id); cur=self.connection.execute('insert into club_debts(club_id,principal,balance,interest,due_date,creditor,origin) values(?,?,?,?,?,?,?)',(club_id,principal,principal,interest,due_date,creditor,origin)); self.connection.execute('update club_economic_state set debt=debt+?,updated_at=? where club_id=?',(principal,date.today().isoformat(),club_id)); self.connection.commit(); return int(cur.lastrowid)
 def declare_bankruptcy(self,club_id,context:WorldTickContext):
  health=self.health(club_id); status=BankruptcyStatus.BANKRUPT.value if health==FinancialHealth.INSOLVENT else BankruptcyStatus.RECOVERY.value if health in (FinancialHealth.CRITICAL,FinancialHealth.WARNING) else BankruptcyStatus.NORMAL.value
  self.connection.execute('update club_economic_state set financial_status=?,updated_at=? where club_id=?',(status,context.current_date.isoformat(),club_id)); self.connection.execute('insert into club_financial_history(club_id,event_type,event_date,payload) values(?,?,?,?)',(club_id,'FINANCIAL_STATUS',context.current_date.isoformat(),status)); self.connection.commit(); return status
 def invest(self,club_id,investor,value,percentage,context:WorldTickContext,type_='CAPITAL_INJECTION'):
  with self.connection:
   self.ledger.post(context,club_id,'INCOME','OTHER',value,'investment',investor,'Investment'); self.connection.execute('insert into investments(club_id,investor,value,percentage,investment_date,type) values(?,?,?,?,?,?)',(club_id,investor,value,percentage,context.current_date.isoformat(),type_)); self.connection.execute('update club_economic_state set cash=cash+?,revenue_accumulated=revenue_accumulated+?,updated_at=? where club_id=?',(value,value,context.current_date.isoformat(),club_id)); return True
 def buy_control(self,club_id,owner_name,owner_type,participation,context:WorldTickContext):
  self.connection.execute("update club_ownership set status='HISTORICAL',end_date=? where club_id=? and status='ACTIVE'",(context.current_date.isoformat(),club_id)); self.connection.execute('insert into club_ownership(club_id,owner_type,owner_name,participation,start_date,status) values(?,?,?,?,?,?)',(club_id,owner_type,owner_name,participation,context.current_date.isoformat(),'ACTIVE')); self.connection.execute('insert into club_financial_history(club_id,event_type,event_date,payload) values(?,?,?,?)',(club_id,'CONTROL_CHANGE',context.current_date.isoformat(),owner_name)); self.connection.commit()
 def close(self): self.connection.close()


class WorldEconomyService:
 """Orquestra receita comercial e folha no mesmo ciclo semanal.

 Cada subsistema mantém sua própria chave de idempotência, impedindo que uma
 repetição do tick duplique receitas de patrocínio ou despesas de folha.
 """
 def __init__(self,db):
  if not isinstance(db,sqlite3.Connection):
   from engine.core.state_store import assert_mutable_state_path
   assert_mutable_state_path(db)
  self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db; self.connection.row_factory=sqlite3.Row
  from engine.economy.sponsorships import SponsorshipService
  from engine.economy.staff_market import StaffMarketService
  self.sponsorships=SponsorshipService(self.connection); self.staff_market=StaffMarketService(self.connection)
 def process_club_week(self,club_id):
  sponsorship=self.sponsorships.process_week(club_id)
  try: payroll=self.staff_market.process_weekly_costs(club_id)
  except ValueError as error:
   if str(error)!='INSUFFICIENT_CASH': raise
   payroll={'processed':False,'reason':'INSUFFICIENT_CASH','weekly_cost':0}
  return {'club_id':club_id,'sponsorship':sponsorship,'payroll':payroll}
 def process_world_week(self):
  club_ids=[int(row['club_id']) for row in self.connection.execute('select club_id from club_payroll_profiles order by club_id').fetchall()]
  sponsorship_processed=0;payroll_processed=0;insufficient_cash=[]
  for club_id in club_ids:
   result=self.process_club_week(club_id)
   sponsorship_processed+=int(bool(result['sponsorship']['processed']));payroll_processed+=int(bool(result['payroll']['processed']))
   if result['payroll'].get('reason')=='INSUFFICIENT_CASH': insufficient_cash.append(club_id)
  return {'clubs_total':len(club_ids),'sponsorship_processed':sponsorship_processed,'payroll_processed':payroll_processed,'insufficient_cash_club_ids':insufficient_cash}
 def close(self): self.connection.close()
