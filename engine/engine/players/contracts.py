from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from engine.core.state_store import assert_mutable_state_path
from engine.world.time_and_finance import FinanceLedger, WorldTickContext


class PlayerContractService:
    """Writer autorizado para renovar contratos no GameState; nunca abre o banco-base."""

    def __init__(self, state_db: str | Path | sqlite3.Connection):
        if isinstance(state_db, sqlite3.Connection):
            self.connection = state_db
            self.connection.row_factory = sqlite3.Row
        else:
            assert_mutable_state_path(state_db)
            self.connection = sqlite3.connect(str(state_db))
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys=ON")

    def close(self) -> None:
        self.connection.close()

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

    def _table_exists(self, table: str) -> bool:
        return self.connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None
