from __future__ import annotations

import sqlite3
from pathlib import Path

from engine.core.domain_errors import DomainError, DomainErrorCode


class StateDatabaseError(DomainError):
    """Raised when a mutable service is pointed at the immutable source database."""

    def __init__(self) -> None:
        super().__init__(DomainErrorCode.IMMUTABLE_BASE_DATABASE)


def assert_mutable_state_path(database: str | Path) -> None:
    path = Path(database).expanduser().resolve()
    if path.name == "game.db" and path.parent.name == "database" and path.parent.parent.name == "data":
        raise StateDatabaseError()


def configure_state_connection(connection: sqlite3.Connection) -> sqlite3.Connection:
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def open_mutable_state(database: str | Path) -> sqlite3.Connection:
    assert_mutable_state_path(database)
    return configure_state_connection(sqlite3.connect(str(database)))
