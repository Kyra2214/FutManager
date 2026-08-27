from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from engine.core.state_store import assert_mutable_state_path
from engine.world.time_and_finance import FinanceLedger, WorldTickContext


class PlayerContractService:
    """Writer autorizado para renovar contratos no GameState; nunca abre o banco-base."""
    SCHEMA = '''
    CREATE TABLE IF NOT EXISTS squad_player_registration(player_id INTEGER NOT NULL,club_id INTEGER NOT NULL,season INTEGER NOT NULL,registration_status TEXT NOT NULL DEFAULT 'PENDING',foreign_player INTEGER NOT NULL DEFAULT 0,shirt_number INTEGER,minutes_promise INTEGER NOT NULL DEFAULT 0,leadership_role TEXT NOT NULL DEFAULT 'SQUAD',PRIMARY KEY(player_id,club_id,season),UNIQUE(club_id,season,shirt_number));
    CREATE TABLE IF NOT EXISTS player_contract_bonuses(bonus_id INTEGER PRIMARY KEY AUTOINCREMENT,player_id INTEGER NOT NULL,club_id INTEGER NOT NULL,contract_id INTEGER,bonus_type TEXT NOT NULL,amount INTEGER NOT NULL,threshold INTEGER NOT NULL DEFAULT 0,progress INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'ACTIVE',UNIQUE(player_id,club_id,contract_id,bonus_type));
    CREATE TABLE IF NOT EXISTS player_release_clauses(player_id INTEGER NOT NULL,club_id INTEGER NOT NULL,contract_id INTEGER NOT NULL,amount INTEGER NOT NULL,PRIMARY KEY(player_id,club_id,contract_id));
    CREATE TABLE IF NOT EXISTS player_contract_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT,contract_id INTEGER NOT NULL,event_type TEXT NOT NULL,season INTEGER NOT NULL,week INTEGER NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(contract_id,event_type,season,week));
    '''

    def __init__(self, state_db: str | Path | sqlite3.Connection):
        if isinstance(state_db, sqlite3.Connection):
            self.connection = state_db
            self.connection.row_factory = sqlite3.Row
        else:
            assert_mutable_state_path(state_db)
            self.connection = sqlite3.connect(str(state_db))
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(self.SCHEMA)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def preview_renewal(self, player_id: int, club_id: int, weekly_salary: int, duration_weeks: int = 52, signing_fee: int = 0, bonus: int = 0) -> dict:
        if min(int(weekly_salary),int(duration_weeks),int(signing_fee),int(bonus))<0 or int(duration_weeks)<1: raise ValueError('CONTRACT_TERMS_INVALID')
        active=self.connection.execute("SELECT contract_id,weekly_salary,end_season,end_week FROM player_contract_history WHERE player_id=? AND club_id=? AND status IN ('ACTIVE','ATIVO','active') ORDER BY contract_id DESC LIMIT 1",(player_id,club_id)).fetchone()
        payroll=self.connection.execute('SELECT weekly_player_payroll FROM club_payroll_profiles WHERE club_id=?',(club_id,)).fetchone() if self._table_exists('club_payroll_profiles') else None
        return {'player_id':int(player_id),'club_id':int(club_id),'active_contract_id':int(active['contract_id']) if active else None,'current_salary':int(active['weekly_salary']) if active else 0,'proposed_salary':int(weekly_salary),'projected_payroll':int(payroll[0]) if payroll else None,'costs':{'signing_fee':int(signing_fee),'bonus':int(bonus)},'persisted':False}

    def terminate_early(self, contract_id: int, season: int, week: int, reason: str) -> dict:
        if not str(reason).strip(): raise ValueError('TERMINATION_REASON_REQUIRED')
        row=self.connection.execute('SELECT * FROM player_contract_history WHERE contract_id=?',(contract_id,)).fetchone()
        if not row: raise KeyError(contract_id)
        with self.connection:
            self.connection.execute("UPDATE player_contract_history SET status='TERMINATED',end_season=?,end_week=? WHERE contract_id=? AND status IN ('ACTIVE','ATIVO','active')",(season,week,contract_id))
            self.connection.execute('INSERT OR IGNORE INTO player_contract_events(contract_id,event_type,season,week,reason,created_at) VALUES(?,?,?,?,?,?)',(contract_id,'TERMINATION',season,week,reason,date.today().isoformat()))
        return dict(self.connection.execute('SELECT * FROM player_contract_history WHERE contract_id=?',(contract_id,)).fetchone())

    def salary_history(self, player_id: int, club_id: int | None = None) -> list[dict]:
        query='SELECT * FROM player_contract_history WHERE player_id=?'; args=[player_id]
        if club_id is not None: query+=' AND club_id=?'; args.append(club_id)
        return [dict(row) for row in self.connection.execute(query+' ORDER BY contract_id',args).fetchall()]

    def contract_audit(self, player_id: int, club_id: int | None = None) -> dict:
        return {'player_id':int(player_id),'contracts':self.salary_history(player_id,club_id),'events':[dict(row) for row in self.connection.execute('SELECT e.* FROM player_contract_events e JOIN player_contract_history h ON h.contract_id=e.contract_id WHERE h.player_id=? ORDER BY e.event_id',(player_id,)).fetchall()],'persisted':True}

    def approve_renewal(
        self,
        *,
        player_id: int,
        club_id: int,
        season: int,
        week: int,
        weekly_salary: int,
        duration_weeks: int = 52,
        signing_fee: int = 0,
        bonus: int = 0,
        manager_approved: bool = False,
        tick_id: str | None = None,
    ) -> dict:
        if not manager_approved:
            raise ValueError("MANAGER_APPROVAL_REQUIRED")
        if min(weekly_salary, duration_weeks, signing_fee, bonus) < 0 or duration_weeks < 1:
            raise ValueError("CONTRACT_TERMS_INVALID")
        self.connection.execute("BEGIN")
        try:
            active = self.connection.execute(
                "SELECT contract_id, weekly_salary FROM player_contract_history WHERE player_id=? AND club_id=? AND status IN ('ACTIVE','ATIVO','active') ORDER BY contract_id DESC LIMIT 1",
                (player_id, club_id),
            ).fetchone()
            if active is None:
                raise ValueError("ACTIVE_CONTRACT_NOT_FOUND")
            profile = self.connection.execute(
                "SELECT salary_limit, strategy FROM club_ai_profiles WHERE club_id=?",
                (club_id,),
            ).fetchone() if self._table_exists("club_ai_profiles") else None
            payroll = self.connection.execute(
                "SELECT weekly_player_payroll FROM club_payroll_profiles WHERE club_id=?",
                (club_id,),
            ).fetchone() if self._table_exists("club_payroll_profiles") else None
            current_payroll = int(payroll[0]) if payroll else 0
            salary_limit = int(profile[0]) if profile and profile[0] is not None else 0
            projected_payroll = current_payroll - int(active["weekly_salary"]) + weekly_salary
            if salary_limit > 0 and projected_payroll > salary_limit:
                raise ValueError("SALARY_CAP_EXCEEDED")
            self.connection.execute("UPDATE player_contract_history SET status='REPLACED', end_season=?, end_week=? WHERE contract_id=?", (season, week, active["contract_id"]))
            end_season = season + (week - 1 + duration_weeks) // 52
            end_week = (week - 1 + duration_weeks) % 52 + 1
            cur = self.connection.execute(
                "INSERT INTO player_contract_history(player_id,club_id,start_season,start_week,end_season,end_week,weekly_salary,release_clause,status,source) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (player_id, club_id, season, week, end_season, end_week, weekly_salary, None, "ACTIVE", "manager_renewal"),
            )
            if self._table_exists("club_payroll_profiles"):
                self.connection.execute("UPDATE club_payroll_profiles SET weekly_player_payroll=? WHERE club_id=?", (projected_payroll, club_id))
            if (signing_fee or bonus) and self._table_exists("financial_ledger"):
                context = WorldTickContext(tick_id or f"{season}:{week}:contract:{player_id}", date.today(), season, week, date.today().month, "week", None)
                ledger = FinanceLedger(self.connection)
                if signing_fee:
                    ledger.post(context, club_id, "EXPENSE", "CONTRACT_SIGNING", -signing_fee, "PLAYER_CONTRACT", f"{cur.lastrowid}:signing", "Luvas de renovação")
                if bonus:
                    ledger.post(context, club_id, "EXPENSE", "CONTRACT_BONUS", -bonus, "PLAYER_CONTRACT", f"{cur.lastrowid}:bonus", "Bônus de renovação")
            self.connection.commit()
            return {"status": "APPROVED", "contract_id": int(cur.lastrowid), "player_id": player_id, "club_id": club_id, "weekly_salary": weekly_salary, "weekly_payroll": projected_payroll, "end_season": end_season, "end_week": end_week}
        except Exception:
            self.connection.rollback()
            raise

    def register_player(self, player_id: int, club_id: int, season: int, foreign_player: bool = False, shirt_number: int | None = None, status: str = 'REGISTERED') -> dict:
        if int(shirt_number or 0) < 0 or status not in ('PENDING','REGISTERED','SUSPENDED'): raise ValueError('REGISTRATION_INVALID')
        occupant=self.connection.execute('SELECT player_id FROM squad_player_registration WHERE club_id=? AND season=? AND shirt_number=? AND player_id<>?',(club_id,season,shirt_number,player_id)).fetchone()
        if occupant is not None: raise ValueError('SHIRT_NUMBER_UNAVAILABLE')
        try:
            with self.connection:
                self.connection.execute('INSERT INTO squad_player_registration(player_id,club_id,season,registration_status,foreign_player,shirt_number) VALUES(?,?,?,?,?,?) ON CONFLICT(player_id,club_id,season) DO UPDATE SET registration_status=excluded.registration_status,foreign_player=excluded.foreign_player,shirt_number=excluded.shirt_number',(player_id,club_id,season,status,int(foreign_player),shirt_number))
        except sqlite3.IntegrityError as error:
            raise ValueError('SHIRT_NUMBER_UNAVAILABLE') from error
        return dict(self.connection.execute('SELECT * FROM squad_player_registration WHERE player_id=? AND club_id=? AND season=?',(player_id,club_id,season)).fetchone())

    def set_squad_role(self, player_id: int, club_id: int, season: int, role: str, minutes_promise: int = 0) -> dict:
        if int(minutes_promise) < 0 or not str(role).strip(): raise ValueError('SQUAD_ROLE_INVALID')
        with self.connection: self.connection.execute('UPDATE squad_player_registration SET leadership_role=?,minutes_promise=? WHERE player_id=? AND club_id=? AND season=?',(role,int(minutes_promise),player_id,club_id,season))
        row=self.connection.execute('SELECT * FROM squad_player_registration WHERE player_id=? AND club_id=? AND season=?',(player_id,club_id,season)).fetchone()
        if not row: raise KeyError(player_id)
        return dict(row)

    def set_release_clause(self, player_id: int, club_id: int, contract_id: int, amount: int) -> dict:
        if int(amount)<0: raise ValueError('RELEASE_CLAUSE_INVALID')
        with self.connection: self.connection.execute('INSERT OR REPLACE INTO player_release_clauses VALUES(?,?,?,?)',(player_id,club_id,contract_id,amount))
        return dict(self.connection.execute('SELECT * FROM player_release_clauses WHERE player_id=? AND club_id=? AND contract_id=?',(player_id,club_id,contract_id)).fetchone())

    def add_contract_bonus(self, player_id: int, club_id: int, contract_id: int, bonus_type: str, amount: int, threshold: int = 0) -> dict:
        if int(amount)<0 or int(threshold)<0 or not str(bonus_type).strip(): raise ValueError('BONUS_INVALID')
        with self.connection: self.connection.execute('INSERT OR REPLACE INTO player_contract_bonuses(player_id,club_id,contract_id,bonus_type,amount,threshold) VALUES(?,?,?,?,?,?)',(player_id,club_id,contract_id,bonus_type,amount,threshold))
        return dict(self.connection.execute('SELECT * FROM player_contract_bonuses WHERE player_id=? AND club_id=? AND contract_id=? AND bonus_type=?',(player_id,club_id,contract_id,bonus_type)).fetchone())

    def progress_bonus(self, bonus_id: int, progress: int) -> dict:
        row=self.connection.execute('SELECT * FROM player_contract_bonuses WHERE bonus_id=?',(bonus_id,)).fetchone()
        if not row or int(progress)<0: raise ValueError('BONUS_PROGRESS_INVALID')
        status='ACHIEVED' if int(progress)>=int(row['threshold']) else row['status']
        with self.connection: self.connection.execute('UPDATE player_contract_bonuses SET progress=?,status=? WHERE bonus_id=?',(progress,status,bonus_id))
        return dict(self.connection.execute('SELECT * FROM player_contract_bonuses WHERE bonus_id=?',(bonus_id,)).fetchone())

    def _table_exists(self, table: str) -> bool:
        return self.connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None
