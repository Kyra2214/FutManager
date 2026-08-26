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

    def season_audit(self, season: int) -> dict:
        return {'season': season, 'currency': self.CURRENCY, 'world': self.world_report(season), 'clubs': [self.report_club(int(row['club_id']), season) for row in self.connection.execute('SELECT DISTINCT club_id FROM financial_ledger WHERE season=? AND club_id IS NOT NULL ORDER BY club_id', (season,)).fetchall()]}
