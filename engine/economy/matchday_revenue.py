from __future__ import annotations

from datetime import date
import sqlite3
from contextlib import nullcontext

from engine.social.attendance import AttendanceService
from engine.world.time_and_finance import FinanceLedger, WorldTickContext

SCHEMA = """
CREATE TABLE IF NOT EXISTS competition_prize_configs (
  competition_id INTEGER NOT NULL,
  rank INTEGER NOT NULL CHECK(rank >= 1),
  prize_amount INTEGER NOT NULL CHECK(prize_amount >= 0),
  PRIMARY KEY(competition_id, rank)
);
CREATE TABLE IF NOT EXISTS competition_prize_runs (
  competition_id INTEGER NOT NULL,
  club_id INTEGER NOT NULL,
  rank INTEGER NOT NULL,
  season INTEGER NOT NULL,
  prize_amount INTEGER NOT NULL,
  awarded_at TEXT NOT NULL,
  PRIMARY KEY(competition_id, club_id)
);
"""


class MatchdayRevenueService:
    def __init__(self, database: str | sqlite3.Connection):
        if not isinstance(database, sqlite3.Connection):
            from engine.core.state_store import assert_mutable_state_path
            assert_mutable_state_path(database)
        self.connection = sqlite3.connect(database) if not isinstance(database, sqlite3.Connection) else database
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(SCHEMA)
        self.attendance = AttendanceService(self.connection)
        self.ledger = FinanceLedger(self.connection)
        self.connection.commit()

    def _cash_credit(self, club_id: int, value: int, current_date: date) -> None:
        state = self.connection.execute("SELECT 1 FROM club_economic_state WHERE club_id=?", (club_id,)).fetchone()
        if not state:
            raise ValueError("ECONOMY_NOT_INITIALIZED")
        self.connection.execute("UPDATE club_economic_state SET cash=cash+?,updated_at=? WHERE club_id=?", (value, current_date.isoformat(), club_id))

    def record_matchday(self, match_id: int, context: WorldTickContext, importance: int = 50, competition_factor: float = 1.0, managed_transaction: bool = True) -> dict:
        match = self.connection.execute("SELECT * FROM matches WHERE match_id=?", (match_id,)).fetchone()
        if not match or match["status"] != "PLAYED":
            raise ValueError("MATCH_NOT_PLAYED")
        attendance = self.attendance.estimate(match_id, int(match["home_club_id"]), int(match["away_club_id"]), importance, competition_factor, seed=(context.seed or 0) + match_id, managed_transaction=managed_transaction)
        reference = str(match_id)
        revenue = attendance.actual * attendance.ticket_price
        with (self.connection if managed_transaction else nullcontext()):
            posted = self.ledger.post(context, int(match["home_club_id"]), "INCOME", "MATCHDAY", revenue, "attendance", reference, "Bilheteria de partida como mandante")
            if not posted:
                return {"status": "ALREADY_PROCESSED", "match_id": match_id, "revenue": revenue}
            self._cash_credit(int(match["home_club_id"]), revenue, context.current_date)
            self.connection.execute("UPDATE attendance_records SET revenue=? WHERE match_id=?", (revenue, match_id))
        return {"status": "PROCESSED", "match_id": match_id, "club_id": int(match["home_club_id"]), "attendance": attendance.actual, "ticket_price": attendance.ticket_price, "revenue": revenue}

    def configure_prize(self, competition_id: int, rank: int, prize_amount: int) -> None:
        if rank < 1 or prize_amount < 0:
            raise ValueError("INVALID_PRIZE_CONFIG")
        with self.connection:
            self.connection.execute("INSERT INTO competition_prize_configs(competition_id,rank,prize_amount) VALUES(?,?,?) ON CONFLICT(competition_id,rank) DO UPDATE SET prize_amount=excluded.prize_amount", (competition_id, rank, prize_amount))

    def award_completed_competition(self, competition_id: int, context: WorldTickContext, managed_transaction: bool = True) -> dict:
        competition = self.connection.execute("SELECT * FROM competitions WHERE competition_id=?", (competition_id,)).fetchone()
        if not competition:
            raise ValueError("COMPETITION_NOT_FOUND")
        pending = self.connection.execute("SELECT COUNT(*) FROM matches WHERE competition_id=? AND status!='PLAYED'", (competition_id,)).fetchone()[0]
        if pending:
            return {"status": "NOT_FINISHED", "awards": []}
        standings = self.connection.execute("SELECT * FROM team_competition_stats WHERE competition_id=? ORDER BY points DESC,wins DESC,(goals_for-goals_against) DESC,goals_for DESC,club_id", (competition_id,)).fetchall()
        prizes = {int(row["rank"]): int(row["prize_amount"]) for row in self.connection.execute("SELECT * FROM competition_prize_configs WHERE competition_id=?", (competition_id,)).fetchall()}
        awards = []
        with (self.connection if managed_transaction else nullcontext()):
            for index, row in enumerate(standings, start=1):
                amount = prizes.get(index, 0)
                if amount <= 0:
                    continue
                club_id = int(row["club_id"])
                existing = self.connection.execute("SELECT 1 FROM competition_prize_runs WHERE competition_id=? AND club_id=?", (competition_id, club_id)).fetchone()
                if existing:
                    continue
                source_id = f"{competition_id}:{club_id}:{index}"
                posted = self.ledger.post(context, club_id, "INCOME", "COMPETITION_PRIZE", amount, "competition_prize", source_id, f"Premiação de classificação: posição {index}")
                if not posted:
                    continue
                self._cash_credit(club_id, amount, context.current_date)
                self.connection.execute("INSERT INTO competition_prize_runs(competition_id,club_id,rank,season,prize_amount,awarded_at) VALUES(?,?,?,?,?,?)", (competition_id, club_id, index, context.season, amount, context.current_date.isoformat()))
                awards.append({"club_id": club_id, "rank": index, "amount": amount})
            self.connection.execute("UPDATE competitions SET status='COMPLETED' WHERE competition_id=?", (competition_id,))
        return {"status": "PROCESSED" if awards else "ALREADY_PROCESSED", "awards": awards}
