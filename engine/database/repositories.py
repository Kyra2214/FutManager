from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class Database:
    def __init__(self, path: str | Path):
        # Repository supports read-only canonical access to data/database/game.db.
        # Mutations must use domain services, which enforce mutable GameState paths.
        self.path = Path(path)
        self.connection: sqlite3.Connection | None = None

    def open(self) -> sqlite3.Connection:
        if self.connection is None:
            self.connection = sqlite3.connect(self.path)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA foreign_keys=ON")
        return self.connection

    def close(self) -> None:
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def integrity_check(self) -> str:
        return str(self.open().execute("PRAGMA integrity_check").fetchone()[0])

    def foreign_key_errors(self) -> list[sqlite3.Row]:
        return list(self.open().execute("PRAGMA foreign_key_check"))


class BaseRepository:
    def __init__(self, database: Database):
        self.database = database

    def _one(self, query: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        return self.database.open().execute(query, params).fetchone()

    def _all(self, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        return list(self.database.open().execute(query, params))


class PlayerRepository(BaseRepository):
    def get(self, player_id: int) -> sqlite3.Row | None:
        return self._one("SELECT * FROM jogadores WHERE jogador_id = ?", (player_id,))

    def search(self, name: str, limit: int = 50) -> list[sqlite3.Row]:
        return self._all("SELECT * FROM jogadores WHERE nome LIKE ? ORDER BY nome LIMIT ?", (f"%{name}%", limit))

    def list_by_country(self, country_id: int, limit: int = 1000) -> list[sqlite3.Row]:
        return self._all("SELECT * FROM vw_jogadores_por_pais WHERE pais_id = ? ORDER BY nome LIMIT ?", (country_id, limit))


class TeamRepository(BaseRepository):
    def get(self, team_id: int) -> sqlite3.Row | None:
        return self._one("SELECT * FROM times WHERE time_id = ?", (team_id,))

    def search(self, name: str, limit: int = 50) -> list[sqlite3.Row]:
        return self._all("SELECT * FROM times WHERE nome LIKE ? ORDER BY nome LIMIT ?", (f"%{name}%", limit))

    def list_by_country(self, country_id: int, limit: int = 1000) -> list[sqlite3.Row]:
        return self._all("SELECT * FROM vw_times_por_pais WHERE pais_id = ? ORDER BY nome LIMIT ?", (country_id, limit))

    def players(self, team_id: int, limit: int = 1000) -> list[sqlite3.Row]:
        return self._all("""SELECT j.*, jt.categoria, jt.status, jt.status_codigo
                          FROM jogadores j JOIN jogador_time jt ON jt.jogador_id=j.jogador_id
                          WHERE jt.time_id=? ORDER BY j.nome LIMIT ?""", (team_id, limit))


class CountryRepository(BaseRepository):
    def get(self, country_id: int) -> sqlite3.Row | None:
        return self._one("SELECT * FROM paises WHERE pais_id = ?", (country_id,))

    def list(self, limit: int = 500) -> list[sqlite3.Row]:
        return self._all("SELECT * FROM paises ORDER BY nome LIMIT ?", (limit,))


class TeamPlayerRepository(BaseRepository):
    def teams_for_player(self, player_id: int, limit: int = 1000) -> list[sqlite3.Row]:
        return self._all("""SELECT t.*, jt.categoria, jt.status, jt.status_codigo
                          FROM times t JOIN jogador_time jt ON jt.time_id=t.time_id
                          WHERE jt.jogador_id=? ORDER BY t.nome LIMIT ?""", (player_id, limit))


class PlayerAttributeRepository(BaseRepository):
    def get_native_attributes(self, player_id: int) -> sqlite3.Row | None:
        return self._one("SELECT jogador_id, cr1, cr2, estrela, top_mundial, lado FROM jogadores WHERE jogador_id=?", (player_id,))
