import sqlite3

from engine.social.attendance import AttendanceService
from engine.social.stadium_fans import SocialService


def state():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    social = SocialService(connection)
    social.create_stadium(1, "Casa", 20_000)
    social.create_stadium(2, "Visitante", 12_000)
    social.ensure_fan_reputation(1, size=18_000)
    social.ensure_fan_reputation(2, size=8_000)
    return connection


def test_match_result_moves_social_metrics_gradually_and_once():
    connection = state()
    service = SocialService(connection)
    before = connection.execute("SELECT satisfaction,size FROM club_fan_base WHERE club_id=1").fetchone()
    result = service.apply_match_result(10, 1, 2, 0, importance=80)
    after = connection.execute("SELECT satisfaction,size FROM club_fan_base WHERE club_id=1").fetchone()
    assert result["status"] == "UPDATED"
    assert after["satisfaction"] > before["satisfaction"]
    assert abs(after["size"] - before["size"]) < before["size"] * 0.02
    assert service.apply_match_result(10, 1, 2, 0, importance=80)["status"] == "ALREADY_PROCESSED"


def test_attendance_is_seeded_limited_by_capacity_and_idempotent():
    connection = state()
    service = AttendanceService(connection)
    service.configure_ticket_price(1, 40)
    first = service.estimate(22, 1, 2, importance=90, competition_factor=1.1, seed=77)
    again = service.estimate(22, 1, 2, importance=90, competition_factor=1.1, seed=7)
    assert 0 <= first.actual <= first.capacity
    assert first.ticket_price > 0
    assert first.actual == again.actual
    assert connection.execute("SELECT COUNT(*) FROM attendance_records WHERE match_id=22").fetchone()[0] == 1
