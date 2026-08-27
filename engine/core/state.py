from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
import shutil

from engine.database.repositories import Database


@dataclass
class WorldState:
    countries: list[int] = field(default_factory=list)
    teams: list[int] = field(default_factory=list)
    competitions: list[int] = field(default_factory=list)
    active_player_ids: list[int] = field(default_factory=list)
    calendar: dict = field(default_factory=dict)
    market: dict = field(default_factory=dict)


@dataclass
class GameState:
    current_date: date
    current_season: str
    controlled_team_id: int | None
    country_id: int | None
    world_state: WorldState
    database_path: Path

    @classmethod
    def initialize(cls, database_path: str | Path, country_id: int | None = None,
                   controlled_team_id: int | None = None) -> "GameState":
        path = Path(database_path)
        db = Database(path)
        db.open()
        season = "inicial"
        return cls(date.today(), season, controlled_team_id, country_id, WorldState(), path)


class PersistenceService:
    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)

    def create_career(self, state_path: str | Path) -> Path:
        destination = Path(state_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.database_path, destination)
        return destination

    def load(self, state_path: str | Path, **kwargs) -> GameState:
        return GameState.initialize(state_path, **kwargs)

    def save(self, state: GameState) -> None:
        # O banco inicial é somente leitura nesta etapa; a persistência de carreira será expandida depois.
        state.database_path.parent.mkdir(parents=True, exist_ok=True)

    def close(self, state: GameState) -> None:
        return None
