from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import random
import sqlite3
from contextlib import nullcontext

from engine.social.stadium_fans import SocialService
from engine.core.domain_errors import DomainError, DomainErrorCode

SCHEMA = """
CREATE TABLE IF NOT EXISTS ticket_price_configs (
  club_id INTEGER PRIMARY KEY,
  base_price INTEGER NOT NULL CHECK(base_price >= 1),
  updated_at TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class AttendanceEstimate:
    expected: int
    actual: int
    capacity: int
    ticket_price: int
    demand: float


class AttendanceService:
    """Público de jogo derivado de dados sociais e de estádio, sem valor no frontend."""

    def __init__(self, database: str | sqlite3.Connection):
        if not isinstance(database, sqlite3.Connection):
            from engine.core.state_store import assert_mutable_state_path
            assert_mutable_state_path(database)
        self.connection = sqlite3.connect(database) if not isinstance(database, sqlite3.Connection) else database
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(SCHEMA)
        self.social = SocialService(self.connection)
        self.connection.commit()

    def configure_ticket_price(self, club_id: int, base_price: int) -> None:
        if base_price < 1 or base_price > 2_000:
            raise DomainError(DomainErrorCode.INVALID_TICKET_PRICE)
        with self.connection:
            self.connection.execute("INSERT INTO ticket_price_configs(club_id,base_price,updated_at) VALUES(?,?,?) ON CONFLICT(club_id) DO UPDATE SET base_price=excluded.base_price,updated_at=excluded.updated_at", (club_id, base_price, date.today().isoformat()))

    def _price(self, club_id: int, importance: int, competition_factor: float, demand: float) -> int:
        configured = self.connection.execute("SELECT base_price FROM ticket_price_configs WHERE club_id=?", (club_id,)).fetchone()
        base = int(configured["base_price"]) if configured else 35
        modifier = 1 + min(0.30, max(-0.15, (importance - 50) / 250)) + min(0.12, max(-0.08, (demand - 0.55) / 6))
        return max(1, int(round(base * competition_factor * modifier)))

    def estimate(self, match_id: int, home_club_id: int, away_club_id: int, importance: int = 50, competition_factor: float = 1.0, seed: int | None = None, managed_transaction: bool = True) -> AttendanceEstimate:
        existing = self.connection.execute("SELECT * FROM attendance_records WHERE match_id=?", (match_id,)).fetchone()
        if existing:
            capacity = self.connection.execute("SELECT usable_capacity FROM club_stadiums WHERE club_id=? AND is_primary=1", (home_club_id,)).fetchone()
            return AttendanceEstimate(int(existing["expected_attendance"]), int(existing["actual_attendance"]), int(capacity[0] if capacity else existing["actual_attendance"]), int(existing["ticket_price"]), float(existing["occupancy_rate"]))
        self.social.ensure_fan_reputation(home_club_id, managed_transaction=managed_transaction)
        self.social.ensure_fan_reputation(away_club_id, managed_transaction=managed_transaction)
        stadium = self.connection.execute("SELECT usable_capacity,comfort,security,quality FROM club_stadiums WHERE club_id=? AND is_primary=1 AND status='ACTIVE'", (home_club_id,)).fetchone()
        if not stadium:
            raise DomainError(DomainErrorCode.STADIUM_NOT_INITIALIZED)
        fan = self.connection.execute("SELECT * FROM club_fan_base WHERE club_id=?", (home_club_id,)).fetchone()
        home_rep = self.connection.execute("SELECT * FROM club_reputation WHERE club_id=?", (home_club_id,)).fetchone()
        away_rep = self.connection.execute("SELECT sporting,national FROM club_reputation WHERE club_id=?", (away_club_id,)).fetchone()
        capacity = max(1, int(stadium["usable_capacity"]))
        fan_pressure = min(1.35, max(0.05, int(fan["size"]) / capacity))
        social = (int(fan["satisfaction"]) * 0.35 + int(fan["engagement"]) * 0.20 + int(fan["interest"]) * 0.15 + int(home_rep["sporting"]) * 0.15 + int(home_rep["commercial"]) * 0.05 + int(stadium["comfort"]) * 0.05 + int(stadium["security"]) * 0.025 + int(stadium["quality"]) * 0.025) / 100
        opponent = ((int(away_rep["sporting"]) + int(away_rep["national"])) / 200) * 0.15
        demand = min(1.0, max(0.02, 0.12 + fan_pressure * 0.45 + social * 0.32 + opponent + max(0, min(100, importance)) / 1000))
        ticket_price = self._price(home_club_id, importance, competition_factor, demand)
        expected = max(0, min(capacity, int(round(capacity * demand))))
        rng = random.Random(seed if seed is not None else match_id)
        actual = max(0, min(capacity, int(round(expected * (0.96 + rng.random() * 0.08)))))
        with (self.connection if managed_transaction else nullcontext()):
            self.connection.execute("INSERT INTO attendance_records(match_id,club_id,expected_attendance,actual_attendance,occupancy_rate,ticket_price,revenue,seed) VALUES(?,?,?,?,?,?,?,?)", (match_id, home_club_id, expected, actual, actual / capacity, ticket_price, actual * ticket_price, seed if seed is not None else match_id))
        return AttendanceEstimate(expected, actual, capacity, ticket_price, demand)
