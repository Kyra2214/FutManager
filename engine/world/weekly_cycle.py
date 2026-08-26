from __future__ import annotations

from datetime import date, timedelta
import json
import sqlite3

from engine.competitions.match_engine import CompetitionService
from engine.economy.matchday_revenue import MatchdayRevenueService
from engine.economy.sponsorships import SponsorshipService
from engine.economy.travel_costs import TravelCostService
from engine.economy.staff_market import StaffMarketService
from engine.events.service import ClubEventService
from engine.social.stadium_fans import SocialService
from engine.world.time_and_finance import FinanceLedger, LogicalClock, WorldTickContext
from engine.core.domain_errors import DomainError, DomainErrorCode

SCHEMA = """
CREATE TABLE IF NOT EXISTS weekly_world_runs(
  season INTEGER NOT NULL,
  week INTEGER NOT NULL,
  scope TEXT NOT NULL DEFAULT 'WORLD',
  tick_id TEXT NOT NULL UNIQUE,
  seed INTEGER,
  status TEXT NOT NULL CHECK(status IN ('RUNNING','COMPLETED','ROLLED_BACK')),
  started_at TEXT NOT NULL,
  finished_at TEXT,
  result_json TEXT,
  error TEXT,
  PRIMARY KEY(season,week,scope)
);
CREATE TABLE IF NOT EXISTS weekly_world_audit(
  audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
  season INTEGER NOT NULL,
  week INTEGER NOT NULL,
  step TEXT NOT NULL,
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE(season,week,step)
);
"""


class WeeklyWorldCycleService:
    """Orquestra uma semana do mundo por chave natural, preservando o SQL como estado único."""

    def __init__(self, database: str | sqlite3.Connection):
        if not isinstance(database, sqlite3.Connection):
            from engine.core.state_store import assert_mutable_state_path
            assert_mutable_state_path(database)
        self.connection = sqlite3.connect(database) if not isinstance(database, sqlite3.Connection) else database
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(SCHEMA)
        self.clock = LogicalClock(self.connection)
        self.ledger = FinanceLedger(self.connection)
        self.matches = CompetitionService(self.connection)
        self.social = SocialService(self.connection)
        self.revenue = MatchdayRevenueService(self.connection)
        self.sponsors = SponsorshipService(self.connection)
        self.travel = TravelCostService(self.connection)
        self.staff = StaffMarketService(self.connection)
        self.events = ClubEventService(self.connection)
        self.connection.commit()

    def _next_context(self, seed: int | None) -> WorldTickContext:
        current = self.clock.current()
        next_date = date.fromisoformat(str(current["current_date"])) + timedelta(days=7)
        week = int(current["current_week"]) + 1
        season = int(current["current_season"])
        if week > 52:
            week, season = 1, season + 1
        return WorldTickContext(f"weekly-world:{season}:{week}", next_date, season, week, next_date.month, "week", seed)

    def _audit(self, context: WorldTickContext, step: str, payload: dict) -> None:
        self.connection.execute("INSERT OR REPLACE INTO weekly_world_audit(season,week,step,payload,created_at) VALUES(?,?,?,?,?)", (context.season, context.week, step, json.dumps(payload, sort_keys=True), context.current_date.isoformat()))

    def advance_week(self, seed: int | None = None) -> dict:
        context = self._next_context(seed)
        return self.process_week(context.season, context.week, seed=seed)

    def process_week(self, season: int, week: int, seed: int | None = None) -> dict:
        """Processa uma chave semanal explícita uma única vez, sem permitir saltos no relógio."""
        existing = self.connection.execute("SELECT * FROM weekly_world_runs WHERE season=? AND week=? AND scope='WORLD'", (season, week)).fetchone()
        if existing and existing["status"] == "COMPLETED":
            return {"status": "ALREADY_PROCESSED", "tick_id": existing["tick_id"], "season": season, "week": week, "result": json.loads(existing["result_json"] or "{}")}
        context = self._next_context(seed)
        if (context.season, context.week) != (season, week):
            raise DomainError(DomainErrorCode.WEEK_OUT_OF_SEQUENCE)
        self.connection.execute("INSERT INTO weekly_world_runs(season,week,scope,tick_id,seed,status,started_at) VALUES(?,?,?,?,?,'RUNNING',?) ON CONFLICT(season,week,scope) DO UPDATE SET tick_id=excluded.tick_id,seed=excluded.seed,status='RUNNING',started_at=excluded.started_at,finished_at=NULL,result_json=NULL,error=NULL", (context.season, context.week, "WORLD", context.tick_id, seed, context.current_date.isoformat()))
        self.connection.commit()
        try:
            self.connection.execute("BEGIN IMMEDIATE")
            self.clock.commit_tick(context)
            due = self.connection.execute("SELECT * FROM matches WHERE status='SCHEDULED' AND match_date<=? ORDER BY match_date,match_id", (context.current_date.isoformat(),)).fetchall()
            processed_matches = []
            for match in due:
                result = self.matches.play(int(match["match_id"]), seed=(seed or 0) + int(match["match_id"]), managed_transaction=False)
                importance = min(100, 40 + int(match["round"]) * 4)
                home_social = self.social.apply_match_result(int(match["match_id"]), int(match["home_club_id"]), result.home_goals, result.away_goals, importance, managed_transaction=False)
                away_social = self.social.apply_match_result(int(match["match_id"]), int(match["away_club_id"]), result.away_goals, result.home_goals, importance, managed_transaction=False)
                for club_id, goals_for, goals_against, social_change in (
                    (int(match["home_club_id"]), result.home_goals, result.away_goals, home_social),
                    (int(match["away_club_id"]), result.away_goals, result.home_goals, away_social),
                ):
                    if social_change.get("status") == "UPDATED":
                        self.events.record(
                            club_id,
                            "TORCIDA",
                            "NORMAL",
                            "Torcida reagiu ao resultado",
                            f"A partida terminou {goals_for}–{goals_against}; a satisfação mudou {social_change['satisfaction_delta']:+d}.",
                            f"event:fan-response:{match['match_id']}:{club_id}",
                            origin="weekly_world_cycle",
                            event_date=context.current_date,
                            impact="MATCH_SOCIAL_UPDATE",
                            managed_transaction=False,
                        )
                try:
                    income = self.revenue.record_matchday(int(match["match_id"]), context, importance=importance, managed_transaction=False)
                except ValueError as error:
                    if str(error) != "STADIUM_NOT_INITIALIZED":
                        raise
                    income = {"status": "STADIUM_NOT_INITIALIZED", "revenue": 0}
                if income.get("status") == "PROCESSED":
                    self.events.record(
                        int(match["home_club_id"]),
                        "FINANCEIRO",
                        "NORMAL",
                        "Bilheteria registrada",
                        f"{income['attendance']:,} torcedores geraram R$ {income['revenue']:,} em receita de jogo.",
                        f"event:matchday:{match['match_id']}",
                        origin="weekly_world_cycle",
                        event_date=context.current_date,
                        impact="MATCHDAY_REVENUE",
                        managed_transaction=False,
                    )
                commercial = self.sponsors.record_match_progress_from_state(int(match["match_id"]), context, managed_transaction=False)
                travel = self.travel.post_for_match(int(match["match_id"]), context, managed_transaction=False)
                processed_matches.append({"match_id": int(match["match_id"]), "home_goals": result.home_goals, "away_goals": result.away_goals, "matchday": income.get("revenue", 0), "missions": commercial, "travel": travel})
            competition_ids = [int(row[0]) for row in self.connection.execute("SELECT DISTINCT competition_id FROM matches WHERE status='PLAYED'").fetchall()]
            prizes = [self.revenue.award_completed_competition(competition_id, context, managed_transaction=False) for competition_id in competition_ids]
            for competition_id, prize_result in zip(competition_ids, prizes, strict=True):
                for award in prize_result.get("awards", []):
                    self.events.record(
                        int(award["club_id"]),
                        "COMPETICAO",
                        "HIGH",
                        "Premiação de competição registrada",
                        f"A posição {award['rank']} rendeu R$ {award['amount']:,} ao clube.",
                        f"event:competition-prize:{competition_id}:{award['club_id']}",
                        origin="weekly_world_cycle",
                        event_date=context.current_date,
                        impact="COMPETITION_PRIZE",
                        managed_transaction=False,
                    )
            sponsor_result = self.sponsors.process_week_all(managed_transaction=False)
            payroll_result = self.staff.process_weekly_costs_all(managed_transaction=False)
            for club_id in payroll_result["insufficient_cash_club_ids"]:
                self.events.record(
                    int(club_id),
                    "FINANCEIRO",
                    "CRITICAL",
                    "Folha semanal sem cobertura de caixa",
                    "A cobrança semanal não foi concluída porque o caixa disponível é insuficiente.",
                    f"event:insufficient-cash:{context.season}:{context.week}:{club_id}",
                    origin="weekly_world_cycle",
                    event_date=context.current_date,
                    impact="INSUFFICIENT_CASH",
                    managed_transaction=False,
                )
            ledger_close = self.ledger.close_week(context)
            result = {"matches": len(processed_matches), "match_details": processed_matches, "prizes": prizes, "sponsorship": sponsor_result, "payroll": payroll_result, "ledger_close": ledger_close}
            self._audit(context, "MATCHES", {"processed": len(processed_matches)})
            self._audit(context, "PRIZES", {"competitions": len(prizes)})
            self._audit(context, "SPONSORSHIPS", sponsor_result)
            self._audit(context, "PAYROLL", payroll_result)
            self._audit(context, "TRAVEL", {"matches": len(processed_matches), "costs": [detail.get("travel", {}) for detail in processed_matches]})
            self._audit(context, "LEDGER_CLOSE", ledger_close)
            self.connection.execute("UPDATE weekly_world_runs SET status='COMPLETED',finished_at=?,result_json=? WHERE season=? AND week=? AND scope='WORLD'", (context.current_date.isoformat(), json.dumps(result, sort_keys=True), context.season, context.week))
            self.connection.commit()
            return {"status": "COMPLETED", "tick_id": context.tick_id, "season": context.season, "week": context.week, **result}
        except Exception as error:
            self.connection.rollback()
            self.connection.execute("UPDATE weekly_world_runs SET status='ROLLED_BACK',finished_at=?,error=? WHERE season=? AND week=? AND scope='WORLD'", (context.current_date.isoformat(), str(error), context.season, context.week))
            self.connection.commit()
            raise
