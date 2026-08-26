import sqlite3

from engine.events.service import ClubEventService


def test_club_events_are_idempotent_and_support_read_state(tmp_path):
    database = tmp_path / "events.db"
    service = ClubEventService(database)

    assert service.record(7, "ESTADIO", "NORMAL", "Estrutura evoluiu", "Nível confirmado.", "event:stadium:7:1", origin="test")
    assert not service.record(7, "ESTADIO", "NORMAL", "Estrutura evoluiu", "Nível confirmado.", "event:stadium:7:1", origin="test")
    listing = service.list_for_club(7)
    assert listing["unread_count"] == 1
    assert listing["items"][0]["severity"] == "NORMAL"
    assert not listing["items"][0]["is_read"]

    assert service.mark_read(7, listing["items"][0]["event_id"])
    assert service.list_for_club(7)["unread_count"] == 0
    assert service.connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    service.connection.close()
