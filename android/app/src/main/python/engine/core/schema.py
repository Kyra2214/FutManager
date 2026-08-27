from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

CURRENT_SCHEMA_VERSION = 3

INDEXES = (
    ("idx_matches_club_week", "matches", "home_team_id, away_team_id, scheduled_date"),
    ("idx_financial_ledger_club_week", "financial_ledger", "club_id, season, week"),
    ("idx_financial_ledger_category_source", "financial_ledger", "category, source_type, source_id"),
    ("idx_club_events_club_read_date", "club_events", "club_id, read, created_at"),
    ("idx_attendance_club_match", "attendance_records", "club_id, match_id"),
    ("idx_manager_career_status", "manager_careers", "manager_id, status, current_club_id"),
    ("idx_manager_history_scope", "manager_history", "manager_id, event_date"),
    ("idx_manager_preferences_scope", "manager_preferences", "manager_id, preference_key"),
    ("idx_career_snapshots_scope", "career_snapshots", "career_id, created_at"),
    ("idx_permission_audit_scope", "manager_permission_audit", "manager_id, created_at"),
    ("idx_migration_audit_component", "migration_audit", "component, version"),
)


def _ensure_indexes(connection: sqlite3.Connection) -> None:
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for index_name, table_name, columns in INDEXES:
        if table_name not in tables:
            continue
        available = {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")}
        required = {column.strip() for column in columns.split(",")}
        if required <= available:
            connection.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns})")


def ensure_schema_version(connection: sqlite3.Connection, component: str = "game_state", version: int = CURRENT_SCHEMA_VERSION) -> int:
    """Create/update the schema ledger inside the supplied SQLite GameState connection."""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_versions (
            component TEXT PRIMARY KEY,
            version INTEGER NOT NULL CHECK(version >= 0),
            applied_at TEXT NOT NULL
        )
        """
    )
    row = connection.execute(
        "SELECT version FROM schema_versions WHERE component=?",
        (component,),
    ).fetchone()
    if row is None:
        connection.execute(
            "INSERT INTO schema_versions(component, version, applied_at) VALUES(?,?,?)",
            (component, version, datetime.now(timezone.utc).isoformat()),
        )
        _ensure_indexes(connection)
        return version
    current = int(row[0])
    if version < current:
        raise ValueError(f"SCHEMA_VERSION_REGRESSION:{component}:{current}->{version}")
    if version > current:
        connection.execute(
            "UPDATE schema_versions SET version=?, applied_at=? WHERE component=?",
            (version, datetime.now(timezone.utc).isoformat(), component),
        )
    _ensure_indexes(connection)
    return version
