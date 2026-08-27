from __future__ import annotations

from dataclasses import dataclass
from contextlib import nullcontext
from datetime import date
from pathlib import Path
import sqlite3

from engine.world.time_and_finance import LogicalClock


from engine.core.state_store import assert_mutable_state_path
FORMULA_VERSION = "institutional-overall-v1"
SQUAD_WEIGHT = 0.60
CT_WEIGHT = 0.25
STADIUM_WEIGHT = 0.15
UNKNOWN_STADIUM_BASELINE = 25.0

SCHEMA = """
CREATE TABLE IF NOT EXISTS club_institutional_profiles(
  club_id INTEGER PRIMARY KEY,
  formula_version TEXT NOT NULL,
  squad_score REAL NOT NULL,
  ct_score REAL NOT NULL,
  stadium_score REAL NOT NULL,
  overall_score REAL NOT NULL,
  sponsor_stars INTEGER NOT NULL,
  squad_available INTEGER NOT NULL,
  ct_available INTEGER NOT NULL,
  stadium_available INTEGER NOT NULL,
  updated_at TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class InstitutionalProfile:
    club_id: int
    squad_score: float
    ct_score: float
    stadium_score: float
    overall_score: float
    sponsor_stars: int
    squad_available: bool
    ct_available: bool
    stadium_available: bool


class InstitutionalPowerService:
    """Calcula o overall comercial sem depender de estado de interface.

    Valores ausentes não são inventados como registros reais: o estádio sem
    infraestrutura detalhada recebe somente a base de regra `25`, indicando que
    o clube possui um estádio nomeado mas ainda não possui medição estrutural.
    """

    def __init__(self, db: str | Path | sqlite3.Connection):
        assert_mutable_state_path(db) if not isinstance(db, sqlite3.Connection) else None
        self.connection = sqlite3.connect(str(db)) if not isinstance(db, sqlite3.Connection) else db
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self.clock = LogicalClock(self.connection)
        self.connection.commit()

    def close(self):
        self.connection.close()

    def _table_exists(self, table: str) -> bool:
        return self.connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone() is not None

    def _column_exists(self, table: str, column: str) -> bool:
        if not self._table_exists(table):
            return False
        return any(row["name"] == column for row in self.connection.execute(f"PRAGMA table_info({table})").fetchall())

    def _squad_score(self, club_id: int) -> tuple[float, bool]:
        if self._table_exists("club_payroll_profiles"):
            stored = self.connection.execute(
                "SELECT team_power FROM club_payroll_profiles WHERE club_id=?", (club_id,)
            ).fetchone()
            if stored is not None:
                return float(stored["team_power"]), True
        membership_columns = {row[1] for row in self.connection.execute("PRAGMA table_info(jogador_time)")}
        player_columns = {row[1] for row in self.connection.execute("PRAGMA table_info(jogadores)")}
        status_expr = "membership.status='Titular'" if 'status' in membership_columns else "0"
        star_expr = "player.estrela=1" if 'estrela' in player_columns else "0"
        world_expr = "player.top_mundial=1" if 'top_mundial' in player_columns else "0"
        row = self.connection.execute(
            f"""SELECT AVG((player.cr1 + player.cr2) / 2.0) AS average_cr,
                      AVG(CASE WHEN {status_expr} THEN (player.cr1 + player.cr2) / 2.0 END) AS starter_average_cr,
                      SUM(CASE WHEN {star_expr} THEN 1 ELSE 0 END) AS stars,
                      SUM(CASE WHEN {world_expr} THEN 1 ELSE 0 END) AS world_class
               FROM jogador_time membership
               JOIN jogadores player ON player.jogador_id=membership.jogador_id
               WHERE membership.time_id=?""",
            (club_id,),
        ).fetchone()
        if row is None or row["average_cr"] is None:
            return 0.0, False
        core = float(row["starter_average_cr"] or row["average_cr"]) * 10
        bonus = min(12, int(row["stars"] or 0) * 1.2) + min(8, int(row["world_class"] or 0) * 2)
        return min(100.0, max(25.0, core + bonus)), True

    def _ct_score(self, club_id: int) -> tuple[float, bool]:
        department_score: float | None = None
        staff_score: float | None = None
        if self._table_exists("club_departments"):
            row = self.connection.execute(
                "SELECT AVG(level) AS average_level FROM club_departments WHERE club_id=?", (club_id,)
            ).fetchone()
            if row and row["average_level"] is not None:
                department_score = min(100.0, max(0.0, float(row["average_level"]) * 10))
        if self._table_exists("staff_members"):
            row = self.connection.execute(
                "SELECT AVG(reputation) AS average_reputation FROM staff_members WHERE club_id=? AND status='ativo'",
                (club_id,),
            ).fetchone()
            if row and row["average_reputation"] is not None:
                staff_score = min(100.0, max(0.0, float(row["average_reputation"])))
        if department_score is None and staff_score is None:
            return 0.0, False
        if department_score is None:
            return float(staff_score), True
        if staff_score is None:
            return float(department_score), True
        return department_score * 0.70 + staff_score * 0.30, True

    def _stadium_score(self, club_id: int) -> tuple[float, bool]:
        if self._table_exists("club_stadiums"):
            row = self.connection.execute(
                "SELECT capacity,level FROM club_stadiums WHERE club_id=? AND is_primary=1 LIMIT 1", (club_id,)
            ).fetchone()
            if row is not None:
                capacity = min(100.0, max(0.0, float(row["capacity"] or 0) / 800.0))
                level = min(100.0, max(0.0, float(row["level"] or 0) * 10.0))
                return capacity * 0.70 + level * 0.30, True
        if self._column_exists("times", "estadio"):
            row = self.connection.execute("SELECT estadio FROM times WHERE time_id=?", (club_id,)).fetchone()
            if row is not None and isinstance(row["estadio"], str) and row["estadio"].strip():
                return UNKNOWN_STADIUM_BASELINE, False
        return 0.0, False

    @staticmethod
    def _stars(overall_score: float) -> int:
        return max(1, min(5, int(overall_score // 20) + 1))

    def refresh(self, club_id: int, managed_transaction: bool = True) -> InstitutionalProfile:
        squad_score, squad_available = self._squad_score(club_id)
        ct_score, ct_available = self._ct_score(club_id)
        stadium_score, stadium_available = self._stadium_score(club_id)
        overall_score = min(100.0, max(0.0, squad_score * SQUAD_WEIGHT + ct_score * CT_WEIGHT + stadium_score * STADIUM_WEIGHT))
        stars = self._stars(overall_score)
        now = self.clock.current()["current_date"]
        with (self.connection if managed_transaction else nullcontext()):
            self.connection.execute(
                """INSERT INTO club_institutional_profiles VALUES(?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(club_id) DO UPDATE SET formula_version=excluded.formula_version,
                     squad_score=excluded.squad_score,ct_score=excluded.ct_score,stadium_score=excluded.stadium_score,
                     overall_score=excluded.overall_score,sponsor_stars=excluded.sponsor_stars,
                     squad_available=excluded.squad_available,ct_available=excluded.ct_available,
                     stadium_available=excluded.stadium_available,updated_at=excluded.updated_at""",
                (club_id, FORMULA_VERSION, squad_score, ct_score, stadium_score, overall_score, stars,
                 int(squad_available), int(ct_available), int(stadium_available), now),
            )
        return InstitutionalProfile(club_id, squad_score, ct_score, stadium_score, overall_score, stars, squad_available, ct_available, stadium_available)

    def get(self, club_id: int) -> InstitutionalProfile | None:
        row = self.connection.execute(
            "SELECT * FROM club_institutional_profiles WHERE club_id=?", (club_id,)
        ).fetchone()
        if row is None:
            return None
        return InstitutionalProfile(
            int(row["club_id"]), float(row["squad_score"]), float(row["ct_score"]),
            float(row["stadium_score"]), float(row["overall_score"]), int(row["sponsor_stars"]),
            bool(row["squad_available"]), bool(row["ct_available"]), bool(row["stadium_available"]),
        )
