import sqlite3

import pytest

from engine.core.safe_undo import SafeUndoService


def test_safe_undo_is_explicit_and_idempotent():
    connection = sqlite3.connect(":memory:")
    service = SafeUndoService(connection)
    registered = service.register_training_plan(17)
    first = service.undo(registered["undo_id"])
    second = service.undo(registered["undo_id"])
    assert first["status"] == "UNDONE"
    assert second["idempotent"] is True


def test_unknown_undo_target_is_rejected():
    connection = sqlite3.connect(":memory:")
    service = SafeUndoService(connection)
    with pytest.raises(KeyError):
        service.undo(999)
