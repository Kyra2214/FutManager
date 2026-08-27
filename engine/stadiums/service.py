from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import sqlite3

from engine.world.time_and_finance import FinanceLedger, LogicalClock, WorldTickContext
from engine.events.service import ClubEventService
from engine.core.domain_errors import DomainError, DomainErrorCode

COMPONENTS = ("arquibancada", "campo", "estrutura", "equipes")
MAX_LEVEL = 10
STARTER_CAPACITY = 12_000

COMPONENT_CONFIG = {
    "arquibancada": {"base_cost": 90_000, "cost_step": 65_000, "base_maintenance": 1_400, "maintenance_step": 750, "capacity_step": 2_250},
    "campo": {"base_cost": 55_000, "cost_step": 40_000, "base_maintenance": 900, "maintenance_step": 520, "capacity_step": 0},
    "estrutura": {"base_cost": 75_000, "cost_step": 55_000, "base_maintenance": 1_150, "maintenance_step": 670, "capacity_step": 0},
    "equipes": {"base_cost": 48_000, "cost_step": 36_000, "base_maintenance": 1_050, "maintenance_step": 610, "capacity_step": 0},
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS club_stadiums(
  stadium_id INTEGER PRIMARY KEY AUTOINCREMENT,
  club_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  capacity INTEGER NOT NULL,
  usable_capacity INTEGER NOT NULL,
  state INTEGER NOT NULL DEFAULT 100,
  level INTEGER NOT NULL DEFAULT 1,
  comfort INTEGER NOT NULL DEFAULT 50,
  security INTEGER NOT NULL DEFAULT 50,
  quality INTEGER NOT NULL DEFAULT 50,
  maintenance_cost INTEGER NOT NULL DEFAULT 0,
  construction_date TEXT NOT NULL,
  last_maintenance TEXT,
  status TEXT NOT NULL DEFAULT 'ACTIVE',
  is_primary INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS stadium_components (
  stadium_id INTEGER NOT NULL,
  component TEXT NOT NULL CHECK(component IN ('arquibancada','campo','estrutura','equipes')),
  level INTEGER NOT NULL DEFAULT 1 CHECK(level BETWEEN 1 AND 10),
  updated_at TEXT NOT NULL,
  PRIMARY KEY(stadium_id, component)
);
CREATE TABLE IF NOT EXISTS stadium_component_history (
  history_id INTEGER PRIMARY KEY AUTOINCREMENT,
  stadium_id INTEGER NOT NULL,
  component TEXT NOT NULL,
  from_level INTEGER NOT NULL,
  to_level INTEGER NOT NULL,
  cost INTEGER NOT NULL,
  maintenance_after INTEGER NOT NULL,
  event_date TEXT NOT NULL,
  reference TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_stadium_components_stadium ON stadium_components(stadium_id);
"""


@dataclass(frozen=True)
class ComponentOffer:
    component: str
    level: int
    next_level: int | None
    upgrade_cost: int | None
    maintenance: int


class StadiumService:
    """Estádio econômico persistido; todos os parâmetros ficam neste módulo versionado."""

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
        self.events = ClubEventService(self.connection)
        self.connection.commit()

    def _source_name(self, club_id: int) -> str | None:
        columns = {str(row[1]) for row in self.connection.execute("PRAGMA table_info(times)").fetchall()}
        if "estadio" not in columns:
            return None
        row = self.connection.execute("SELECT estadio FROM times WHERE time_id=?", (club_id,)).fetchone()
        return str(row["estadio"]).strip() if row and row["estadio"] else None

    def bootstrap_club(self, club_id: int, name: str | None = None, capacity: int = STARTER_CAPACITY) -> dict:
        """Cria estádio apenas por ação explícita; não é chamado por leituras."""
        if capacity <= 0:
            raise ValueError("INVALID_CAPACITY")
        existing = self.connection.execute("SELECT stadium_id FROM club_stadiums WHERE club_id=? AND is_primary=1", (club_id,)).fetchone()
        if existing:
            self._ensure_components(int(existing["stadium_id"]))
            return self.get_stadium(club_id) or {}
        stadium_name = name or self._source_name(club_id)
        if not stadium_name:
            raise ValueError("STADIUM_SOURCE_MISSING")
        today = str(self.clock.current()["current_date"])
        with self.connection:
            cursor = self.connection.execute(
                """INSERT INTO club_stadiums(club_id,name,capacity,usable_capacity,state,level,comfort,security,quality,maintenance_cost,construction_date,last_maintenance,status,is_primary)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,1)""",
                (club_id, stadium_name, capacity, capacity, 100, 1, 10, 10, 10, self._maintenance_for_levels({component: 1 for component in COMPONENTS}), today, today, "ACTIVE"),
            )
            stadium_id = int(cursor.lastrowid)
            for component in COMPONENTS:
                self.connection.execute("INSERT INTO stadium_components(stadium_id,component,level,updated_at) VALUES(?,?,1,?)", (stadium_id, component, today))
        return self.get_stadium(club_id) or {}

    def bootstrap_all_clubs(self) -> dict:
        columns = {str(row[1]) for row in self.connection.execute("PRAGMA table_info(times)").fetchall()}
        if "estadio" not in columns:
            return {"clubs_total": 0, "created": 0, "reconciled": 0, "skipped": 0, "reason": "STADIUM_SOURCE_MISSING"}
        rows = self.connection.execute("SELECT time_id,estadio FROM times WHERE estadio IS NOT NULL AND trim(estadio)!='' ORDER BY time_id").fetchall()
        created = reconciled = skipped = 0
        for row in rows:
            club_id = int(row["time_id"])
            stadium = self.connection.execute("SELECT stadium_id FROM club_stadiums WHERE club_id=? AND is_primary=1", (club_id,)).fetchone()
            component_count = int(self.connection.execute("SELECT COUNT(*) FROM stadium_components WHERE stadium_id=?", (stadium["stadium_id"],)).fetchone()[0]) if stadium else 0
            self.bootstrap_club(club_id, str(row["estadio"]))
            if not stadium:
                created += 1
            elif component_count < len(COMPONENTS):
                reconciled += 1
            else:
                skipped += 1
        return {"clubs_total": len(rows), "created": created, "reconciled": reconciled, "skipped": skipped}

    def _ensure_components(self, stadium_id: int) -> None:
        """Reconcilia registros do módulo social criado antes dos componentes."""
        stadium = self.connection.execute("SELECT level FROM club_stadiums WHERE stadium_id=?", (stadium_id,)).fetchone()
        if not stadium:
            raise KeyError("STADIUM_NOT_FOUND")
        legacy_level = min(MAX_LEVEL, max(1, int(stadium["level"] or 1)))
        today = str(self.clock.current()["current_date"])
        with self.connection:
            for component in COMPONENTS:
                self.connection.execute(
                    "INSERT OR IGNORE INTO stadium_components(stadium_id,component,level,updated_at) VALUES(?,?,?,?)",
                    (stadium_id, component, legacy_level, today),
                )
            self._sync_aggregate(stadium_id, self._levels(stadium_id))

    def _levels(self, stadium_id: int) -> dict[str, int]:
        rows = self.connection.execute("SELECT component,level FROM stadium_components WHERE stadium_id=?", (stadium_id,)).fetchall()
        return {str(row["component"]): int(row["level"]) for row in rows}

    @staticmethod
    def _component_cost(component: str, target_level: int) -> int:
        config = COMPONENT_CONFIG[component]
        return int(config["base_cost"] + (target_level - 1) * config["cost_step"])

    @staticmethod
    def _component_maintenance(component: str, level: int) -> int:
        config = COMPONENT_CONFIG[component]
        return int(config["base_maintenance"] + (level - 1) * config["maintenance_step"])

    def _maintenance_for_levels(self, levels: dict[str, int]) -> int:
        return sum(self._component_maintenance(component, levels.get(component, 1)) for component in COMPONENTS)

    def _capacity_for_levels(self, base_capacity: int, levels: dict[str, int]) -> int:
        return int(base_capacity + (levels["arquibancada"] - 1) * COMPONENT_CONFIG["arquibancada"]["capacity_step"])

    def _sync_aggregate(self, stadium_id: int, levels: dict[str, int]) -> None:
        stadium = self.connection.execute("SELECT capacity FROM club_stadiums WHERE stadium_id=?", (stadium_id,)).fetchone()
        if not stadium:
            raise KeyError("STADIUM_NOT_FOUND")
        # O valor em capacity permanece como capacidade-base; usable_capacity é a capacidade operacional atual.
        base_capacity = max(1, int(stadium["capacity"]))
        usable = self._capacity_for_levels(base_capacity, levels)
        overall = round(sum(levels.values()) / len(COMPONENTS))
        self.connection.execute(
            """UPDATE club_stadiums SET usable_capacity=?,level=?,comfort=?,security=?,quality=?,maintenance_cost=? WHERE stadium_id=?""",
            (usable, overall, min(100, levels["estrutura"] * 10), min(100, levels["equipes"] * 10), min(100, levels["campo"] * 10), self._maintenance_for_levels(levels), stadium_id),
        )

    def get_stadium(self, club_id: int) -> dict | None:
        stadium = self.connection.execute("SELECT * FROM club_stadiums WHERE club_id=? AND is_primary=1 AND status='ACTIVE'", (club_id,)).fetchone()
        if not stadium:
            return None
        levels = self._levels(int(stadium["stadium_id"]))
        if set(levels) != set(COMPONENTS):
            return None
        offers = []
        for component in COMPONENTS:
            level = levels[component]
            target = level + 1 if level < MAX_LEVEL else None
            offers.append(ComponentOffer(component, level, target, self._component_cost(component, target) if target else None, self._component_maintenance(component, level)).__dict__)
        return {
            "stadium_id": int(stadium["stadium_id"]), "club_id": int(stadium["club_id"]), "name": stadium["name"],
            "base_capacity": int(stadium["capacity"]), "capacity": int(stadium["usable_capacity"]),
            "maintenance": int(stadium["maintenance_cost"]), "matchday_quality": round((levels["campo"] * 0.35 + levels["estrutura"] * 0.35 + levels["equipes"] * 0.30) * 10, 1),
            "components": offers,
            "history": [dict(row) for row in self.connection.execute("SELECT * FROM stadium_component_history WHERE stadium_id=? ORDER BY history_id DESC LIMIT 12", (stadium["stadium_id"],)).fetchall()],
        }

    def _context(self, club_id: int, component: str, level: int) -> WorldTickContext:
        now = self.clock.current()
        return WorldTickContext(f"stadium:{club_id}:{component}:{level}", date.fromisoformat(str(now["current_date"])), int(now["current_season"]), int(now["current_week"]), int(now["current_month"]), "stadium")

    def preview_stadium_upgrade(self, club_id: int, component: str) -> dict:
        if component not in COMPONENTS:
            raise ValueError("INVALID_STADIUM_COMPONENT")
        stadium = self.connection.execute("SELECT * FROM club_stadiums WHERE club_id=? AND is_primary=1 AND status='ACTIVE'", (club_id,)).fetchone()
        if not stadium:
            raise DomainError(DomainErrorCode.STADIUM_NOT_INITIALIZED)
        levels = self._levels(int(stadium["stadium_id"]))
        current_level = levels.get(component)
        if current_level is None:
            raise ValueError("STADIUM_COMPONENT_MISSING")
        if current_level >= MAX_LEVEL:
            raise ValueError("STADIUM_COMPONENT_MAX_LEVEL")
        target_level = current_level + 1
        cost = self._component_cost(component, target_level)
        levels[component] = target_level
        cash = self.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=?", (club_id,)).fetchone()
        if not cash:
            raise ValueError("ECONOMY_NOT_INITIALIZED")
        return {"club_id": club_id, "component": component, "from_level": current_level, "target_level": target_level, "cost": cost, "maintenance_before": int(stadium["maintenance_cost"]), "maintenance_after": self._maintenance_for_levels(levels), "cash_before": int(cash["cash"]), "cash_after": int(cash["cash"])-cost, "cash_sufficient": int(cash["cash"]) >= cost, "persisted": False, "formula_version": "stadium-upgrade-preview-v1"}

    def upgrade_stadium_component(self, club_id: int, component: str) -> dict:
        if component not in COMPONENTS:
            raise ValueError("INVALID_STADIUM_COMPONENT")
        stadium = self.connection.execute("SELECT * FROM club_stadiums WHERE club_id=? AND is_primary=1 AND status='ACTIVE'", (club_id,)).fetchone()
        if not stadium:
            raise DomainError(DomainErrorCode.STADIUM_NOT_INITIALIZED)
        levels = self._levels(int(stadium["stadium_id"]))
        current_level = levels.get(component)
        if current_level is None:
            raise ValueError("STADIUM_COMPONENT_MISSING")
        if current_level >= MAX_LEVEL:
            raise ValueError("STADIUM_COMPONENT_MAX_LEVEL")
        target_level = current_level + 1
        cost = self._component_cost(component, target_level)
        economic = self.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=?", (club_id,)).fetchone()
        if not economic:
            raise ValueError("ECONOMY_NOT_INITIALIZED")
        if int(economic["cash"]) < cost:
            raise DomainError(DomainErrorCode.INSUFFICIENT_CASH)
        reference = f"stadium:{int(stadium['stadium_id'])}:{component}:{target_level}"
        context = self._context(club_id, component, target_level)
        with self.connection:
            posted = self.ledger.post(context, club_id, "EXPENSE", "STADIUM_UPGRADE", -cost, "stadium_component", reference, f"Evolução de {component} para nível {target_level}")
            if not posted:
                raise DomainError(DomainErrorCode.ALREADY_PROCESSED)
            self.connection.execute("UPDATE club_economic_state SET cash=cash-?,updated_at=? WHERE club_id=?", (cost, context.current_date.isoformat(), club_id))
            self.connection.execute("UPDATE stadium_components SET level=?,updated_at=? WHERE stadium_id=? AND component=?", (target_level, context.current_date.isoformat(), stadium["stadium_id"], component))
            levels[component] = target_level
            self._sync_aggregate(int(stadium["stadium_id"]), levels)
            self.connection.execute(
                """INSERT INTO stadium_component_history(stadium_id,component,from_level,to_level,cost,maintenance_after,event_date,reference)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (stadium["stadium_id"], component, current_level, target_level, cost, self._maintenance_for_levels(levels), context.current_date.isoformat(), reference),
            )
            self.events.record(
                club_id,
                "ESTADIO",
                "NORMAL",
                f"{component.title()} evoluiu para o nível {target_level}",
                f"O estádio recebeu uma evolução de R$ {cost:,} na operação {component}.",
                f"event:{reference}",
                origin="stadium_service",
                event_date=context.current_date,
                impact="STADIUM_UPGRADE",
                managed_transaction=False,
            )
        return {"component": component, "from_level": current_level, "target_level": target_level, "cost": cost, "stadium": self.get_stadium(club_id)}
