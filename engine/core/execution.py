from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class ExecutionContext:
    """Contrato imutável de uma execução do motor; não é estado de jogo."""

    tick_id: str
    current_date: date
    season: int
    week: int
    seed: int | None
    scope: str = "WORLD"

    def __post_init__(self) -> None:
        if not self.tick_id.strip():
            raise ValueError("TICK_ID_REQUIRED")
        if self.season < 0 or self.week < 0:
            raise ValueError("EXECUTION_PERIOD_INVALID")
        if self.scope not in {"WORLD", "CLUB", "COMPETITION"}:
            raise ValueError("EXECUTION_SCOPE_INVALID")

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["current_date"] = self.current_date.isoformat()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ExecutionContext":
        return cls(
            tick_id=str(payload["tick_id"]),
            current_date=date.fromisoformat(str(payload["current_date"])),
            season=int(payload["season"]),
            week=int(payload["week"]),
            seed=None if payload.get("seed") is None else int(payload["seed"]),
            scope=str(payload.get("scope", "WORLD")),
        )
