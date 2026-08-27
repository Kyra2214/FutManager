from __future__ import annotations
from datetime import date
from pathlib import Path
from contextlib import contextmanager
import logging
import sqlite3

from engine.world.time_and_finance import LogicalClock, FinanceLedger, WorldTickContext
from engine.economy.world_economy import EconomyService

from engine.core.state_store import assert_mutable_state_path

logger = logging.getLogger(__name__)
SCHEMA = """
CREATE TABLE IF NOT EXISTS club_finances (club_id INTEGER PRIMARY KEY, cash INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS economic_contracts (
 contract_id INTEGER PRIMARY KEY AUTOINCREMENT, club_id INTEGER, contract_type TEXT NOT NULL,
 category TEXT NOT NULL, amount INTEGER NOT NULL, frequency TEXT NOT NULL DEFAULT 'weekly',
 start_date TEXT NOT NULL, end_date TEXT, status TEXT NOT NULL DEFAULT 'active', description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS facility_obligations (
 obligation_id INTEGER PRIMARY KEY AUTOINCREMENT, club_id INTEGER NOT NULL, category TEXT NOT NULL,
 weekly_amount INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'active', description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS orchestration_audit (
 audit_id INTEGER PRIMARY KEY AUTOINCREMENT, tick_id TEXT NOT NULL, event_type TEXT NOT NULL,
 created_at TEXT NOT NULL, payload TEXT NOT NULL
);
"""

class IntegrationOrchestrator:
    def __init__(self, state_db: str|Path):
        assert_mutable_state_path(state_db);self.connection=sqlite3.connect(state_db)
        self.connection.row_factory=sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.executescript(SCHEMA); self.connection.commit()
        self.clock=LogicalClock(self.connection)
        self.ledger=FinanceLedger(self.connection)
        self.economy=EconomyService(self.connection)

    def add_contract(self, club_id:int, category:str, amount:int, description:str, contract_type='staff', end_date=None, managed_transaction: bool = True):
        self.connection.execute('''INSERT INTO economic_contracts(club_id,contract_type,category,amount,start_date,end_date,description) VALUES(?,?,?,?,?,?,?)''',(club_id,contract_type,category,amount,date.today().isoformat(),end_date,description))
        if managed_transaction: self.connection.commit()

    def add_facility_obligation(self, club_id:int, category:str, weekly_amount:int, description:str, managed_transaction: bool = True):
        self.connection.execute('insert into facility_obligations(club_id,category,weekly_amount,description) values(?,?,?,?)',(club_id,category,weekly_amount,description))
        if managed_transaction: self.connection.commit()

    def ensure_finance(self, club_id:int, cash:int=0, managed_transaction: bool = True):
        self.economy.ensure_club(club_id, cash=cash, budget=0)
        self.connection.execute("INSERT OR REPLACE INTO club_finances(club_id,cash,updated_at) VALUES(?,?,?)", (club_id, cash, date.today().isoformat()))
        if managed_transaction: self.connection.commit()

    def advance_week(self, seed=None, managed_transaction: bool = True) -> WorldTickContext:
        context=self.clock.next_week_context(seed)
        self.process_context(context, managed_transaction=managed_transaction)
        return context

    @contextmanager
    def transaction(self, managed_transaction: bool = True):
        if not managed_transaction:
            yield
            return
        self.connection.execute('BEGIN')
        try:
            yield
        except Exception:
            self.connection.rollback()
            raise
        else:
            self.connection.commit()

    @staticmethod
    def _assert_tick_preconditions(context: WorldTickContext):
        if not context.tick_id or context.season < 1 or not 1 <= context.week <= 52:
            raise ValueError('INVALID_TICK_CONTEXT')

    def process_context(self, context:WorldTickContext, managed_transaction: bool = True):
        self._assert_tick_preconditions(context)
        with self.transaction(managed_transaction):
            self._process_context(context, managed_transaction=False)

    def _process_context(self, context:WorldTickContext, managed_transaction: bool = False):
        logger.info('world_tick_started', extra={'tick_id': context.tick_id, 'season': context.season, 'week': context.week})
        con=self.connection
        try:
            if managed_transaction: con.execute('BEGIN')
            now=context.current_date.isoformat()
            con.execute('insert or ignore into financial_events(tick_id,season,week,event_type,created_at) values(?,?,?,?,?)',(context.tick_id,context.season,context.week,'WORLD_TICK',now))
            movements = {}
            contracts=con.execute("select * from economic_contracts where status='active' and (end_date is null or end_date>=?)",(now,)).fetchall()
            for row in contracts:
                type_='INCOME' if row['contract_type']=='sponsor' else 'EXPENSE'
                category=row['category']
                amount = row['amount'] if type_=='INCOME' else -abs(row['amount'])
                if self.ledger.post(context,row['club_id'],type_,category,amount,'sponsor_contract' if type_=='INCOME' else 'contract',row['contract_id'],row['description']): movements[row['club_id']] = movements.get(row['club_id'], 0) + amount
            facilities=con.execute("select * from facility_obligations where status='active'").fetchall()
            for row in facilities:
                amount = -abs(row['weekly_amount'])
                if self.ledger.post(context,row['club_id'],'EXPENSE','FACILITY_MAINTENANCE',amount,'facility',row['obligation_id'],row['description']): movements[row['club_id']] = movements.get(row['club_id'], 0) + amount
            for club_id, amount in movements.items():
                self.economy.ensure_club(club_id, cash=0, budget=0)
                con.execute('update club_economic_state set cash=cash+?,updated_at=? where club_id=?',(amount,now,club_id))
                if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='club_finances'").fetchone():
                    con.execute('UPDATE club_finances SET cash=(SELECT cash FROM club_economic_state WHERE club_id=?),updated_at=? WHERE club_id=?',(club_id,now,club_id))
            self.clock.commit_tick(context, managed_transaction=False)
            con.execute('insert into orchestration_audit(tick_id,event_type,created_at,payload) values(?,?,?,?,?)' if False else 'insert into orchestration_audit(tick_id,event_type,created_at,payload) values(?,?,?,?)',(context.tick_id,'WEEK_PROCESSED',now,f'{{"season":{context.season},"week":{context.week}}}'))
            logger.info('world_tick_completed', extra={'tick_id': context.tick_id, 'season': context.season, 'week': context.week, 'movement_count': len(movements)})
            if managed_transaction: con.commit()
        except Exception:
            if managed_transaction: con.rollback()
            raise

    def close(self): self.connection.close()
