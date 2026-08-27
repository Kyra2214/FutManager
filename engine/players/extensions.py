from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from engine.core.state_store import assert_mutable_state_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS player_position_aliases (
    player_id INTEGER PRIMARY KEY,
    original_position TEXT NOT NULL,
    normalized_position TEXT NOT NULL,
    source TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(player_id, original_position, normalized_position)
);
CREATE TABLE IF NOT EXISTS player_progression (
    player_id INTEGER NOT NULL,
    season INTEGER NOT NULL CHECK(season >= 0),
    age INTEGER NOT NULL CHECK(age >= 0),
    potential INTEGER,
    source TEXT NOT NULL,
    PRIMARY KEY(player_id, season)
);
CREATE TABLE IF NOT EXISTS player_attribute_history (
    player_id INTEGER NOT NULL,
    season INTEGER NOT NULL CHECK(season >= 0),
    cr1 INTEGER NOT NULL,
    cr2 INTEGER NOT NULL,
    attributes_json TEXT NOT NULL CHECK(json_valid(attributes_json)),
    source TEXT NOT NULL,
    PRIMARY KEY(player_id, season)
);
CREATE TABLE IF NOT EXISTS player_contract_history (
    contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    club_id INTEGER,
    start_season INTEGER NOT NULL,
    start_week INTEGER NOT NULL CHECK(start_week BETWEEN 1 AND 52),
    end_season INTEGER,
    end_week INTEGER CHECK(end_week IS NULL OR end_week BETWEEN 1 AND 52),
    weekly_salary INTEGER NOT NULL CHECK(weekly_salary >= 0),
    release_clause INTEGER CHECK(release_clause IS NULL OR release_clause >= 0),
    status TEXT NOT NULL,
    source TEXT NOT NULL,
    UNIQUE(player_id, club_id, start_season, start_week)
);
CREATE TABLE IF NOT EXISTS player_profile_extensions (
    player_id INTEGER PRIMARY KEY,
    preferred_position TEXT,
    dominant_foot TEXT,
    versatility INTEGER CHECK(versatility IS NULL OR versatility BETWEEN 0 AND 100),
    personality_json TEXT NOT NULL DEFAULT '{}' CHECK(json_valid(personality_json)),
    source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS player_availability (
    player_id INTEGER NOT NULL,
    season INTEGER NOT NULL CHECK(season >= 0),
    week INTEGER NOT NULL CHECK(week BETWEEN 1 AND 52),
    availability_status TEXT NOT NULL,
    suspension_matches INTEGER NOT NULL DEFAULT 0 CHECK(suspension_matches >= 0),
    reason TEXT,
    source TEXT NOT NULL,
    PRIMARY KEY(player_id, season, week)
);
CREATE INDEX IF NOT EXISTS idx_player_progression_player_season ON player_progression(player_id, season);
CREATE INDEX IF NOT EXISTS idx_player_contract_player_status ON player_contract_history(player_id, status);
CREATE INDEX IF NOT EXISTS idx_player_availability_week ON player_availability(season, week, availability_status);
"""


def _now() -> str:
    return '1970-01-01T00:00:00+00:00'


class PlayerCanonicalExtensionService:
    """Persiste apenas extensões explicitamente observadas no GameState mutável."""

    def __init__(self, state_db: str | Path):
        assert_mutable_state_path(state_db)
        self.connection = sqlite3.connect(str(state_db))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    @contextmanager
    def transaction(self, managed_transaction: bool = True) -> Iterator[None]:
        if not managed_transaction:
            yield
            return
        self.connection.execute('BEGIN')
        try:
            yield
        except Exception:
            self.connection.rollback()
            raise
        else:
            self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def upsert_position_alias(self, player_id: int, original_position: str, normalized_position: str, source: str = 'observed', managed_transaction: bool = True) -> None:
        if not original_position.strip() or not normalized_position.strip():
            raise ValueError('POSITION_ALIAS_REQUIRED')
        with self.transaction(managed_transaction):
            self.connection.execute('''INSERT INTO player_position_aliases(player_id,original_position,normalized_position,source,updated_at)
                VALUES(?,?,?,?,?) ON CONFLICT(player_id) DO UPDATE SET original_position=excluded.original_position,
                normalized_position=excluded.normalized_position, source=excluded.source, updated_at=excluded.updated_at''',
                (player_id, original_position.strip(), normalized_position.strip(), source, _now()))

    def record_progression(self, player_id: int, season: int, age: int, potential: int | None, source: str = 'observed', managed_transaction: bool = True) -> None:
        with self.transaction(managed_transaction):
            self.connection.execute('''INSERT INTO player_progression(player_id,season,age,potential,source) VALUES(?,?,?,?,?)
                ON CONFLICT(player_id,season) DO UPDATE SET age=excluded.age,potential=excluded.potential,source=excluded.source''',
                (player_id, season, age, potential, source))

    def record_attributes(self, player_id: int, season: int, cr1: int, cr2: int, attributes: dict[str, Any], source: str = 'observed', managed_transaction: bool = True) -> None:
        payload = json.dumps(attributes, ensure_ascii=False, sort_keys=True)
        with self.transaction(managed_transaction):
            self.connection.execute('''INSERT INTO player_attribute_history(player_id,season,cr1,cr2,attributes_json,source) VALUES(?,?,?,?,?,?)
                ON CONFLICT(player_id,season) DO UPDATE SET cr1=excluded.cr1,cr2=excluded.cr2,attributes_json=excluded.attributes_json,source=excluded.source''',
                (player_id, season, cr1, cr2, payload, source))

    def record_contract(self, player_id: int, club_id: int | None, start_season: int, start_week: int, end_season: int | None, end_week: int | None, weekly_salary: int, release_clause: int | None, status: str, source: str = 'observed', managed_transaction: bool = True) -> None:
        with self.transaction(managed_transaction):
            self.connection.execute('''INSERT INTO player_contract_history(player_id,club_id,start_season,start_week,end_season,end_week,weekly_salary,release_clause,status,source)
                VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(player_id,club_id,start_season,start_week) DO UPDATE SET end_season=excluded.end_season,end_week=excluded.end_week,
                weekly_salary=excluded.weekly_salary,release_clause=excluded.release_clause,status=excluded.status,source=excluded.source''',
                (player_id, club_id, start_season, start_week, end_season, end_week, weekly_salary, release_clause, status, source))

    def record_profile(self, player_id: int, preferred_position: str | None, dominant_foot: str | None, versatility: int | None, personality: dict[str, Any] | None = None, source: str = 'observed', managed_transaction: bool = True) -> None:
        payload = json.dumps(personality or {}, ensure_ascii=False, sort_keys=True)
        with self.transaction(managed_transaction):
            self.connection.execute('''INSERT INTO player_profile_extensions(player_id,preferred_position,dominant_foot,versatility,personality_json,source)
                VALUES(?,?,?,?,?,?) ON CONFLICT(player_id) DO UPDATE SET preferred_position=excluded.preferred_position,dominant_foot=excluded.dominant_foot,
                versatility=excluded.versatility,personality_json=excluded.personality_json,source=excluded.source''',
                (player_id, preferred_position, dominant_foot, versatility, payload, source))

    def record_availability(self, player_id: int, season: int, week: int, availability_status: str, suspension_matches: int = 0, reason: str | None = None, source: str = 'observed', managed_transaction: bool = True) -> None:
        with self.transaction(managed_transaction):
            self.connection.execute('''INSERT INTO player_availability(player_id,season,week,availability_status,suspension_matches,reason,source)
                VALUES(?,?,?,?,?,?,?) ON CONFLICT(player_id,season,week) DO UPDATE SET availability_status=excluded.availability_status,
                suspension_matches=excluded.suspension_matches,reason=excluded.reason,source=excluded.source''',
                (player_id, season, week, availability_status, suspension_matches, reason, source))

    @staticmethod
    def unattached_players(base_db: str | Path) -> list[dict[str, Any]]:
        connection = sqlite3.connect(f'file:{Path(base_db).resolve()}?mode=ro', uri=True)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute('''SELECT p.jogador_id, p.nome, p.posicao, p.pais_id FROM jogadores p
                WHERE NOT EXISTS (SELECT 1 FROM jogador_time jt WHERE jt.jogador_id=p.jogador_id)
                ORDER BY p.jogador_id''').fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    @staticmethod
    def incomplete_squads(base_db: str | Path, minimum_players: int = 11) -> list[dict[str, Any]]:
        if minimum_players < 1:
            raise ValueError('MINIMUM_PLAYERS_INVALID')
        connection = sqlite3.connect(f'file:{Path(base_db).resolve()}?mode=ro', uri=True)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute('''SELECT t.time_id, t.nome, t.pais_id, COUNT(jt.jogador_id) AS player_count
                FROM times t LEFT JOIN jogador_time jt ON jt.time_id=t.time_id
                GROUP BY t.time_id,t.nome,t.pais_id HAVING COUNT(jt.jogador_id) < ? ORDER BY player_count,t.time_id''', (minimum_players,)).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()
