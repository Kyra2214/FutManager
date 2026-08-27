from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import sqlite3
import uuid

SCHEMA = """
CREATE TABLE IF NOT EXISTS logical_clock (
 clock_id INTEGER PRIMARY KEY CHECK(clock_id=1), current_date TEXT NOT NULL,
 current_week INTEGER NOT NULL, current_month INTEGER NOT NULL, current_season INTEGER NOT NULL,
 last_processed_tick TEXT
);
CREATE TABLE IF NOT EXISTS financial_ledger (
 ledger_id INTEGER PRIMARY KEY AUTOINCREMENT, club_id INTEGER, date TEXT NOT NULL,
 season INTEGER NOT NULL, week INTEGER NOT NULL, type TEXT NOT NULL, category TEXT NOT NULL,
 amount INTEGER NOT NULL, description TEXT NOT NULL, source_type TEXT NOT NULL, source_id TEXT NOT NULL,
 tick_id TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(club_id,season,week,category,source_type,source_id)
);
CREATE TABLE IF NOT EXISTS financial_budgets(club_id INTEGER NOT NULL,season INTEGER NOT NULL,week INTEGER NOT NULL,limit_amount INTEGER NOT NULL,PRIMARY KEY(club_id,season,week));
CREATE TABLE IF NOT EXISTS financial_recurring_rules(rule_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,category TEXT NOT NULL,amount INTEGER NOT NULL,source_type TEXT NOT NULL,source_id TEXT NOT NULL,description TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'ACTIVE',UNIQUE(club_id,category,source_type,source_id));
CREATE TABLE IF NOT EXISTS financial_alerts(alert_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,season INTEGER NOT NULL,week INTEGER NOT NULL,alert_type TEXT NOT NULL,message TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(club_id,season,week,alert_type));
CREATE TABLE IF NOT EXISTS financial_events (
 event_id INTEGER PRIMARY KEY AUTOINCREMENT, tick_id TEXT NOT NULL UNIQUE, season INTEGER NOT NULL,
 week INTEGER NOT NULL, event_type TEXT NOT NULL, created_at TEXT NOT NULL
);
"""

@dataclass(frozen=True)
class WorldTickContext:
    tick_id: str
    current_date: date
    season: int
    week: int
    month: int
    advance_type: str = "week"
    seed: int | None = None

class LogicalClock:
    def __init__(self, connection: sqlite3.Connection, start_date: date=date(2026,1,1), season: int=2026):
        self.connection=connection; self.connection.row_factory=sqlite3.Row
        self.connection.executescript(SCHEMA); self.connection.commit()
        if self.connection.execute('select 1 from logical_clock where clock_id=1').fetchone() is None:
            self.connection.execute('insert into logical_clock values (1,?,?,?,?,NULL)',(start_date.isoformat(),1,start_date.month,season)); self.connection.commit()

    def current(self): return self.connection.execute('select * from logical_clock where clock_id=1').fetchone()

    def next_week_context(self, seed=None) -> WorldTickContext:
        row=self.current(); d=date.fromisoformat(row['current_date'])+timedelta(days=7)
        week=row['current_week']+1; season=row['current_season']
        if week>52: week=1; season+=1
        return WorldTickContext(f'{season}:{week}:{uuid.uuid4().hex}',d,season,week,d.month,'week',seed)

    def next_day_context(self, seed=None) -> WorldTickContext:
        row=self.current(); d=date.fromisoformat(row['current_date'])+timedelta(days=1)
        return WorldTickContext(f'{row["current_season"]}:{row["current_week"]}:day:{uuid.uuid4().hex}', d, row['current_season'], row['current_week'], d.month, 'day', seed)

    def commit_tick(self, context: WorldTickContext, managed_transaction: bool = True):
        # O nome preserva a API histórica; a decisão de commit pertence ao coordenador externo.
        self.connection.execute('update logical_clock set current_date=?,current_week=?,current_month=?,current_season=?,last_processed_tick=? where clock_id=1',(context.current_date.isoformat(),context.week,context.month,context.season,context.tick_id))

    def restore(self, current_date: str, week: int, month: int, season: int, tick_id: str | None = None) -> None:
        date.fromisoformat(current_date)
        if week < 1 or week > 52 or month < 1 or month > 12 or season < 1:
            raise ValueError('CLOCK_STATE_INVALID')
        self.connection.execute('UPDATE logical_clock SET current_date=?,current_week=?,current_month=?,current_season=?,last_processed_tick=? WHERE clock_id=1', (current_date, week, month, season, tick_id))

class FinanceLedger:
    CURRENCY = 'BRL'
    CATEGORIES = frozenset({'PAYROLL', 'PLAYER_PAYROLL', 'PLAYER_SALARY', 'SALARY', 'STAFF', 'STAFF_PAYROLL', 'DEPARTMENT', 'DEPARTMENT_MAINTENANCE', 'FACILITY', 'STADIUM_MAINTENANCE', 'FACILITY_MAINTENANCE', 'MATCHDAY', 'MATCHDAY_REVENUE', 'SPONSORSHIP', 'SPONSOR', 'SPONSOR_PAYMENT', 'MEDIA', 'SPONSOR_MISSION', 'SPONSOR_MISSION_REWARD', 'SPONSOR_UPFRONT', 'SPONSOR_WEEKLY', 'COMPETITION_PRIZE', 'PRIZE', 'TRANSFER', 'TRANSFER_FEE', 'TRANSFER_INCOME', 'STADIUM_UPGRADE', 'CONTRACT_SIGNING', 'CONTRACT_BONUS', 'TAX', 'TRAVEL', 'OTHER'})

    def __init__(self, connection):
        self.connection = connection

    def post(self, context: WorldTickContext, club_id:int|None, type_:str, category:str, amount:int, source_type:str, source_id:str, description:str):
        if category not in self.CATEGORIES:
            raise ValueError('LEDGER_CATEGORY_INVALID')
        if not isinstance(amount, int):
            raise ValueError('LEDGER_AMOUNT_MUST_BE_INTEGER')
        cur=self.connection.execute('''INSERT OR IGNORE INTO financial_ledger(club_id,date,season,week,type,category,amount,description,source_type,source_id,tick_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',(club_id,context.current_date.isoformat(),context.season,context.week,type_,category,amount,description,source_type,str(source_id),context.tick_id,context.current_date.isoformat()))
        return cur.rowcount==1

    def close_week(self, context: WorldTickContext) -> dict:
        row = self.connection.execute('SELECT COUNT(*) AS entries, COALESCE(SUM(amount),0) AS net FROM financial_ledger WHERE season=? AND week=?', (context.season, context.week)).fetchone()
        return {'season': context.season, 'week': context.week, 'currency': self.CURRENCY, 'entries': int(row['entries']), 'net': int(row['net'])}

    def report_club(self, club_id: int, season: int | None = None) -> dict:
        where = 'club_id=?' + (' AND season=?' if season is not None else '')
        args = (club_id,) if season is None else (club_id, season)
        rows = self.connection.execute(f'SELECT type, category, COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END),0) AS income, COALESCE(SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END),0) AS expense, COALESCE(SUM(amount),0) AS net FROM financial_ledger WHERE {where} GROUP BY type, category ORDER BY category', args).fetchall()
        income = sum(int(row['income']) for row in rows)
        expense = sum(int(row['expense']) for row in rows)
        return {'club_id': club_id, 'season': season, 'currency': self.CURRENCY, 'income': income, 'expense': expense, 'net': income - expense, 'by_category': [dict(row) for row in rows]}

    def world_report(self, season: int | None = None) -> dict:
        where = '' if season is None else ' WHERE season=?'
        args = () if season is None else (season,)
        row = self.connection.execute(f'SELECT COUNT(*) AS entries, COALESCE(SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END),0) AS income, COALESCE(SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END),0) AS expense FROM financial_ledger{where}', args).fetchone()
        return {'season': season, 'currency': self.CURRENCY, 'entries': int(row['entries']), 'income': int(row['income']), 'expense': int(row['expense']), 'net': int(row['income']) - int(row['expense'])}

    def preview_post(self, context: WorldTickContext, club_id: int | None, type_: str, category: str, amount: int, source_type: str, source_id: str, description: str) -> dict:
        if category not in self.CATEGORIES: raise ValueError('LEDGER_CATEGORY_INVALID')
        if not isinstance(amount, int): raise ValueError('LEDGER_AMOUNT_MUST_BE_INTEGER')
        existing = self.connection.execute('SELECT ledger_id FROM financial_ledger WHERE club_id IS ? AND season=? AND week=? AND category=? AND source_type=? AND source_id=?', (club_id, context.season, context.week, category, source_type, str(source_id))).fetchone()
        return {'club_id': club_id, 'season': context.season, 'week': context.week, 'category': category, 'amount': amount, 'duplicate': existing is not None, 'persisted': False}

    def reconcile_club(self, club_id: int, season: int | None = None) -> dict:
        report = self.report_club(club_id, season)
        duplicate_rows = self.connection.execute('SELECT COUNT(*) AS total FROM (SELECT club_id,season,week,category,source_type,source_id,COUNT(*) c FROM financial_ledger WHERE club_id=? GROUP BY club_id,season,week,category,source_type,source_id HAVING c>1)', (int(club_id),)).fetchone()['total']
        return {**report, 'duplicate_sources': int(duplicate_rows), 'reconciled': int(duplicate_rows) == 0}

    def budget_alert(self, club_id: int, season: int, week: int, limit: int) -> dict:
        row = self.connection.execute('SELECT COALESCE(SUM(CASE WHEN amount < 0 THEN -amount ELSE 0 END),0) AS expense FROM financial_ledger WHERE club_id=? AND season=? AND week=?', (int(club_id), int(season), int(week))).fetchone()
        expense = int(row['expense'])
        return {'club_id': int(club_id), 'season': int(season), 'week': int(week), 'limit': int(limit), 'expense': expense, 'over_limit': expense > int(limit), 'persisted': False}

    def set_budget(self, club_id: int, season: int, week: int, limit_amount: int) -> dict:
        if int(limit_amount)<0: raise ValueError('BUDGET_INVALID')
        with self.connection: self.connection.execute('INSERT OR REPLACE INTO financial_budgets VALUES(?,?,?,?)',(club_id,season,week,limit_amount))
        return dict(self.connection.execute('SELECT * FROM financial_budgets WHERE club_id=? AND season=? AND week=?',(club_id,season,week)).fetchone())

    def add_recurring_rule(self, club_id: int, category: str, amount: int, source_type: str, source_id: str, description: str) -> dict:
        self.post(WorldTickContext('rule-bootstrap',date.today(),1,1,1,'week'),club_id,'INTERNAL',category,0,'RULE',source_id,description) if False else None
        if category not in self.CATEGORIES or not str(source_id).strip(): raise ValueError('RECURRING_RULE_INVALID')
        with self.connection: self.connection.execute('INSERT OR REPLACE INTO financial_recurring_rules(club_id,category,amount,source_type,source_id,description) VALUES(?,?,?,?,?,?)',(club_id,category,amount,source_type,source_id,description))
        return dict(self.connection.execute('SELECT * FROM financial_recurring_rules WHERE club_id=? AND category=? AND source_type=? AND source_id=?',(club_id,category,source_type,source_id)).fetchone())

    def apply_recurring(self, context: WorldTickContext, club_id: int) -> dict:
        rows=self.connection.execute("SELECT * FROM financial_recurring_rules WHERE club_id=? AND status='ACTIVE'",(club_id,)).fetchall(); applied=0
        for row in rows: applied += int(self.post(context,club_id,'INCOME' if int(row['amount'])>=0 else 'EXPENSE',row['category'],int(row['amount']),row['source_type'],row['source_id'],row['description']))
        return {'club_id':int(club_id),'season':context.season,'week':context.week,'applied':applied,'rules':len(rows)}

    def forecast(self, club_id: int, season: int, week: int, weeks: int = 4) -> dict:
        if int(weeks)<1: raise ValueError('FORECAST_WEEKS_INVALID')
        current=self.report_club(club_id,season); recurring=self.connection.execute("SELECT COALESCE(SUM(amount),0) AS net FROM financial_recurring_rules WHERE club_id=? AND status='ACTIVE'",(club_id,)).fetchone()['net']
        projected=current['net'] + int(recurring)*int(weeks)
        return {'club_id':int(club_id),'season':int(season),'week':int(week),'weeks':int(weeks),'current_net':current['net'],'recurring_weekly':int(recurring),'projected_net':projected,'deficit':projected<0,'persisted':False}

    def weekly_balance(self, club_id: int, season: int, week: int) -> dict:
        report=self.report_club(club_id,season); budget=self.connection.execute('SELECT limit_amount FROM financial_budgets WHERE club_id=? AND season=? AND week=?',(club_id,season,week)).fetchone(); alert=self.budget_alert(club_id,season,week,int(budget['limit_amount']) if budget else 0) if budget else None
        return {'club_id':int(club_id),'season':int(season),'week':int(week),'report':report,'budget':dict(budget) if budget else None,'alert':alert}

    def monthly_close(self, club_id: int, season: int, month: int) -> dict:
        if not 1<=int(month)<=12: raise ValueError('MONTH_INVALID')
        rows=self.connection.execute('SELECT category,COALESCE(SUM(amount),0) AS net,COUNT(*) AS entries FROM financial_ledger WHERE club_id=? AND season=? AND CAST(strftime(\'%m\',date) AS INTEGER)=? GROUP BY category ORDER BY category',(club_id,season,month)).fetchall()
        report={'club_id':int(club_id),'season':int(season),'month':int(month),'categories':[dict(r) for r in rows]}
        report['net']=sum(int(r['net']) for r in rows); report['closed']=True; return report

    def cross_domain_reconciliation(self, club_id: int, season: int, source_types: list[str] | None = None) -> dict:
        query='SELECT source_type,COUNT(*) AS entries,COALESCE(SUM(amount),0) AS net FROM financial_ledger WHERE club_id=? AND season=?'; args=[club_id,season]
        if source_types: query+=' AND source_type IN ('+','.join('?' for _ in source_types)+')'; args.extend(source_types)
        rows=self.connection.execute(query+' GROUP BY source_type ORDER BY source_type',args).fetchall()
        return {'club_id':int(club_id),'season':int(season),'sources':[dict(r) for r in rows],'reconciled':all(int(r['entries'])>0 for r in rows) if rows else True}

    def media_revenue_summary(self, club_id: int, season: int) -> dict:
        rows=self.connection.execute("SELECT category,COALESCE(SUM(amount),0) AS net FROM financial_ledger WHERE club_id=? AND season=? AND category IN ('MEDIA','MATCHDAY_REVENUE','SPONSOR','SPONSOR_PAYMENT','COMPETITION_PRIZE','PRIZE','TAX','TRAVEL') GROUP BY category ORDER BY category",(club_id,season)).fetchall()
        return {'club_id':int(club_id),'season':int(season),'by_category':[dict(r) for r in rows],'net':sum(int(r['net']) for r in rows),'persisted':True}

    def season_audit(self, season: int) -> dict:
        return {'season': season, 'currency': self.CURRENCY, 'world': self.world_report(season), 'clubs': [self.report_club(int(row['club_id']), season) for row in self.connection.execute('SELECT DISTINCT club_id FROM financial_ledger WHERE season=? AND club_id IS NOT NULL ORDER BY club_id', (season,)).fetchall()]}
