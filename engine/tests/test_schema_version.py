import shutil
import sqlite3
from pathlib import Path

import pytest

from engine.manager.career import ManagerService

from engine.core.schema import ensure_schema_version


def test_schema_version_is_idempotent_and_monotonic():
    connection = sqlite3.connect(":memory:")
    assert ensure_schema_version(connection) == 2
    assert ensure_schema_version(connection) == 2
    assert ensure_schema_version(connection, version=3) == 3
    row = connection.execute("SELECT component, version FROM schema_versions").fetchone()
    assert row == ("game_state", 3)
    connection.close()


def test_manager_service_initializes_schema_version_in_temporary_gamestate(tmp_path: Path):
    base = Path(__file__).resolve().parents[1] / "data" / "database" / "game.db"
    state = tmp_path / "game.db"
    shutil.copy2(base, state)
    service = ManagerService(state)
    row = service.connection.execute("SELECT version FROM schema_versions WHERE component='game_state'").fetchone()
    assert row[0] == 2
    service.close()


def test_schema_version_creates_indexes_and_preserves_integrity_in_temporary_gamestate(tmp_path: Path):
    base = Path(__file__).resolve().parents[1] / "data" / "database" / "game.db"
    state = tmp_path / "game.db"
    shutil.copy2(base, state)
    connection = sqlite3.connect(state)
    connection.execute("PRAGMA foreign_keys=OFF")
    connection.executescript("""
        DROP TABLE IF EXISTS matches;
        DROP TABLE IF EXISTS financial_ledger;
        DROP TABLE IF EXISTS club_events;
        DROP TABLE IF EXISTS attendance_records;
        CREATE TABLE matches(home_team_id INTEGER, away_team_id INTEGER, scheduled_date TEXT);
        CREATE TABLE financial_ledger(club_id INTEGER, season INTEGER, week INTEGER, category TEXT, source_type TEXT, source_id TEXT);
        CREATE TABLE club_events(club_id INTEGER, read INTEGER, created_at TEXT);
        CREATE TABLE attendance_records(club_id INTEGER, match_id INTEGER);
    """)
    connection.commit()
    connection.close()
    service = ManagerService(state)
    for table, expected in {
        "matches": "idx_matches_club_week",
        "financial_ledger": "idx_financial_ledger_club_week",
        "club_events": "idx_club_events_club_read_date",
        "attendance_records": "idx_attendance_club_match",
    }.items():
        indexes = {row[1] for row in service.connection.execute(f"PRAGMA index_list({table})")}
        assert expected in indexes
    assert service.connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert service.connection.execute("PRAGMA foreign_key_check").fetchall() == []
    service.close()


def test_schema_version_creates_available_cycle_indexes():
    connection = sqlite3.connect(":memory:")
    connection.executescript("""
        CREATE TABLE matches(home_team_id INTEGER, away_team_id INTEGER, scheduled_date TEXT);
        CREATE TABLE financial_ledger(club_id INTEGER, season INTEGER, week INTEGER, category TEXT, source_type TEXT, source_id TEXT);
        CREATE TABLE club_events(club_id INTEGER, read INTEGER, created_at TEXT);
    """)
    ensure_schema_version(connection)
    indexes = {row[1] for row in connection.execute("PRAGMA index_list(matches)")}
    indexes |= {row[1] for row in connection.execute("PRAGMA index_list(financial_ledger)")}
    indexes |= {row[1] for row in connection.execute("PRAGMA index_list(club_events)")}
    assert {"idx_matches_club_week", "idx_financial_ledger_club_week", "idx_financial_ledger_category_source", "idx_club_events_club_read_date"} <= indexes
    connection.close()


def test_schema_version_rejects_regression():
    connection = sqlite3.connect(":memory:")
    ensure_schema_version(connection, version=3)
    with pytest.raises(ValueError, match="SCHEMA_VERSION_REGRESSION"):
        ensure_schema_version(connection, version=2)
    connection.close()
