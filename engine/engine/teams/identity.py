from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from engine.core.state_store import assert_mutable_state_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS club_identity_extensions (
    club_id INTEGER PRIMARY KEY,
    division TEXT,
    region TEXT,
    competition_origin TEXT,
    strength INTEGER CHECK(strength IS NULL OR strength BETWEEN 0 AND 100),
    institutional_overall INTEGER CHECK(institutional_overall IS NULL OR institutional_overall BETWEEN 0 AND 100),
    source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS selection_identity_extensions (
    selection_id INTEGER PRIMARY KEY,
    confederation TEXT,
    region TEXT,
    competition_origin TEXT,
    source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS club_search_aliases (
    club_id INTEGER NOT NULL,
    alias TEXT NOT NULL,
    normalized_alias TEXT NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY(club_id, alias),
    UNIQUE(normalized_alias, club_id)
);
CREATE TABLE IF NOT EXISTS club_rivalries (
    club_id INTEGER NOT NULL,
    rival_club_id INTEGER NOT NULL,
    source_reference TEXT NOT NULL,
    source_documented INTEGER NOT NULL DEFAULT 1 CHECK(source_documented = 1),
    PRIMARY KEY(club_id, rival_club_id),
    CHECK(club_id <> rival_club_id)
);
CREATE TABLE IF NOT EXISTS club_name_history (
    club_id INTEGER NOT NULL,
    historical_name TEXT NOT NULL,
    valid_from_season INTEGER,
    valid_to_season INTEGER,
    source_reference TEXT NOT NULL,
    PRIMARY KEY(club_id, historical_name)
);
CREATE TABLE IF NOT EXISTS club_stadium_identity (
    club_id INTEGER PRIMARY KEY,
    stadium_name TEXT,
    source_reference TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS club_kit_links (
    club_id INTEGER PRIMARY KEY,
    primary_asset_id INTEGER,
    secondary_asset_id INTEGER,
    source_reference TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_club_identity_country_division ON club_identity_extensions(division, region, strength);
CREATE INDEX IF NOT EXISTS idx_club_alias_normalized ON club_search_aliases(normalized_alias);
"""


class ClubIdentityService:
    """Extensões de identidade persistidas no GameState; nunca escreve no banco-base."""

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

    def upsert_club_identity(self, club_id: int, division: str | None, region: str | None, competition_origin: str | None, strength: int | None, institutional_overall: int | None, source: str = 'observed', managed_transaction: bool = True) -> None:
        with self.transaction(managed_transaction):
            self.connection.execute('''INSERT INTO club_identity_extensions(club_id,division,region,competition_origin,strength,institutional_overall,source)
                VALUES(?,?,?,?,?,?,?) ON CONFLICT(club_id) DO UPDATE SET division=excluded.division,region=excluded.region,
                competition_origin=excluded.competition_origin,strength=excluded.strength,institutional_overall=excluded.institutional_overall,source=excluded.source''',
                (club_id, division, region, competition_origin, strength, institutional_overall, source))

    def upsert_selection_identity(self, selection_id: int, confederation: str | None, region: str | None, competition_origin: str | None, source: str = 'observed', managed_transaction: bool = True) -> None:
        with self.transaction(managed_transaction):
            self.connection.execute('''INSERT INTO selection_identity_extensions(selection_id,confederation,region,competition_origin,source)
                VALUES(?,?,?,?,?) ON CONFLICT(selection_id) DO UPDATE SET confederation=excluded.confederation,region=excluded.region,
                competition_origin=excluded.competition_origin,source=excluded.source''',
                (selection_id, confederation, region, competition_origin, source))

    def add_alias(self, club_id: int, alias: str, source: str = 'observed', managed_transaction: bool = True) -> None:
        clean = alias.strip()
        if not clean:
            raise ValueError('CLUB_ALIAS_REQUIRED')
        with self.transaction(managed_transaction):
            self.connection.execute('INSERT OR REPLACE INTO club_search_aliases(club_id,alias,normalized_alias,source) VALUES(?,?,?,?)', (club_id, clean, clean.casefold(), source))

    def record_rivalry(self, club_id: int, rival_club_id: int, source_reference: str, managed_transaction: bool = True) -> None:
        if club_id == rival_club_id or not source_reference.strip():
            raise ValueError('DOCUMENTED_RIVALRY_REQUIRED')
        with self.transaction(managed_transaction):
            self.connection.execute('INSERT OR REPLACE INTO club_rivalries(club_id,rival_club_id,source_reference) VALUES(?,?,?)', (club_id, rival_club_id, source_reference.strip()))

    def record_name_history(self, club_id: int, historical_name: str, source_reference: str, valid_from_season: int | None = None, valid_to_season: int | None = None, managed_transaction: bool = True) -> None:
        if not historical_name.strip() or not source_reference.strip():
            raise ValueError('DOCUMENTED_NAME_HISTORY_REQUIRED')
        with self.transaction(managed_transaction):
            self.connection.execute('INSERT OR REPLACE INTO club_name_history(club_id,historical_name,valid_from_season,valid_to_season,source_reference) VALUES(?,?,?,?,?)', (club_id, historical_name.strip(), valid_from_season, valid_to_season, source_reference.strip()))

    def record_stadium(self, club_id: int, stadium_name: str | None, source_reference: str, managed_transaction: bool = True) -> None:
        if not source_reference.strip():
            raise ValueError('STADIUM_SOURCE_REQUIRED')
        with self.transaction(managed_transaction):
            self.connection.execute('INSERT OR REPLACE INTO club_stadium_identity(club_id,stadium_name,source_reference) VALUES(?,?,?)', (club_id, stadium_name, source_reference.strip()))

    def record_kits(self, club_id: int, primary_asset_id: int | None, secondary_asset_id: int | None, source_reference: str, managed_transaction: bool = True) -> None:
        if not source_reference.strip():
            raise ValueError('KIT_SOURCE_REQUIRED')
        with self.transaction(managed_transaction):
            self.connection.execute('INSERT OR REPLACE INTO club_kit_links(club_id,primary_asset_id,secondary_asset_id,source_reference) VALUES(?,?,?,?)', (club_id, primary_asset_id, secondary_asset_id, source_reference.strip()))

    def list_club_aliases(self, club_id: int | None = None) -> list[dict[str, object]]:
        sql = 'SELECT club_id,alias,normalized_alias,source FROM club_search_aliases'
        args: tuple[object, ...] = ()
        if club_id is not None:
            sql += ' WHERE club_id=?'
            args = (club_id,)
        sql += ' ORDER BY normalized_alias,club_id'
        return [dict(row) for row in self.connection.execute(sql, args).fetchall()]

    def list_clubs(self, base_db: str | Path, country_id: int | None = None, division: str | None = None, min_strength: int | None = None, max_strength: int | None = None) -> list[dict[str, object]]:
        base = sqlite3.connect(f'file:{Path(base_db).resolve()}?mode=ro', uri=True)
        base.row_factory = sqlite3.Row
        try:
            rows = [dict(row) for row in base.execute('SELECT time_id,nome,pais_id,estadio,tipo,arquivo_origem FROM times ORDER BY nome,time_id').fetchall()]
        finally:
            base.close()
        extensions = {row['club_id']: dict(row) for row in self.connection.execute('SELECT club_id,division,region,competition_origin,strength,institutional_overall FROM club_identity_extensions').fetchall()}
        result: list[dict[str, object]] = []
        for row in rows:
            extension = extensions.get(row['time_id'], {})
            if country_id is not None and row['pais_id'] != country_id:
                continue
            if division is not None and extension.get('division') != division:
                continue
            strength = extension.get('strength')
            if min_strength is not None and (strength is None or strength < min_strength):
                continue
            if max_strength is not None and (strength is None or strength > max_strength):
                continue
            result.append({**row, **extension})
        return result

    def list_selections(self, base_db: str | Path, codigo: str | None = None, confederation: str | None = None) -> list[dict[str, object]]:
        base = sqlite3.connect(f'file:{Path(base_db).resolve()}?mode=ro', uri=True)
        base.row_factory = sqlite3.Row
        try:
            rows = [dict(row) for row in base.execute('SELECT selecao_id,codigo,nome,pais_id FROM selecoes ORDER BY nome,selecao_id').fetchall()]
        finally:
            base.close()
        extensions = {row['selection_id']: dict(row) for row in self.connection.execute('SELECT selection_id,confederation,region,competition_origin FROM selection_identity_extensions').fetchall()}
        result: list[dict[str, object]] = []
        for row in rows:
            extension = extensions.get(row['selecao_id'], {})
            if codigo is not None and row['codigo'] != codigo:
                continue
            if confederation is not None and extension.get('confederation') != confederation:
                continue
            result.append({**row, **extension})
        return result

    def get_rivalries(self, club_id: int) -> list[dict[str, object]]:
        return [dict(row) for row in self.connection.execute('SELECT club_id,rival_club_id,source_reference FROM club_rivalries WHERE club_id=? ORDER BY rival_club_id', (club_id,)).fetchall()]
