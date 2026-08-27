import sqlite3
from pathlib import Path

import pytest

from engine.core.state_store import StateDatabaseError, assert_mutable_state_path, open_mutable_state
from engine.manager.career import ManagerService


def test_immutable_base_path_is_rejected():
    base = Path(__file__).resolve().parents[1] / "data" / "database" / "game.db"
    with pytest.raises(StateDatabaseError, match="IMMUTABLE_BASE_DATABASE"):
        ManagerService(base)
    with pytest.raises(StateDatabaseError, match="IMMUTABLE_BASE_DATABASE"):
        assert_mutable_state_path(base)


def test_temporary_state_file_and_memory_connection_are_allowed(tmp_path: Path):
    state = tmp_path / "game.db"
    connection = open_mutable_state(state)
    connection.execute("CREATE TABLE marker(value TEXT)")
    connection.commit()
    connection.close()

    memory = sqlite3.connect(":memory:")
    service = ManagerService(memory)
    assert service.connection.execute("SELECT version FROM schema_versions").fetchone()[0] == 3
    service.close()
