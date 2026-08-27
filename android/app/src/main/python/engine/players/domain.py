from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from datetime import date


class Position(IntEnum):
    GOALKEEPER = 0
    FULLBACK = 1
    CENTER_BACK = 2
    MIDFIELDER = 3
    FORWARD = 4

    @property
    def label(self) -> str:
        return {0: "Goleiro", 1: "Lateral", 2: "Zagueiro", 3: "Meia", 4: "Atacante"}[int(self)]


class PlayerStatus(StrEnum):
    RESERVE = "Reserva"
    STARTER = "Titular"
    INJURED = "Lesionado"
    SUSPENDED = "Suspenso"
    RETIRED = "Aposentado"


@dataclass(frozen=True)
class NativeAttributes:
    cr1: int | None
    cr2: int | None
    rating_hash: int | None
    is_star: bool
    is_top_world: bool
    side: int | None


@dataclass
class PlayerContract:
    club_id: int | None = None
    salary: int | None = None
    market_value: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    release_clause: int | None = None


@dataclass
class PlayerCondition:
    fitness: int | None = None
    morale: int | None = None
    fatigue: int | None = None
    injury: str | None = None
    suspension_matches: int = 0


@dataclass
class PlayerHistoryEntry:
    event_date: date
    event_type: str
    description: str


@dataclass
class Player:
    player_id: int
    name: str | None
    age: int | None
    nationality_id: int | None
    position: Position
    native: NativeAttributes
    contract: PlayerContract = field(default_factory=PlayerContract)
    condition: PlayerCondition = field(default_factory=PlayerCondition)
    status: PlayerStatus = PlayerStatus.RESERVE
    potential: int | None = None
    strength: int | None = None
    history: list[PlayerHistoryEntry] = field(default_factory=list)

    @classmethod
    def from_row(cls, row, status: str | None = None) -> "Player":
        keys = row.keys()
        native_hash = row["rating_hash"] if "rating_hash" in keys else None
        return cls(
            player_id=int(row["jogador_id"]), name=row["nome"], age=row["idade"],
            nationality_id=row["pais_id"], position=Position(int(row["posicao_codigo"])),
            native=NativeAttributes(row["cr1"], row["cr2"], native_hash, bool(row["estrela"]), bool(row["top_mundial"]), row["lado"]),
            status=PlayerStatus(status) if status in {s.value for s in PlayerStatus} else PlayerStatus.RESERVE,
        )
