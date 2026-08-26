import sqlite3

import pytest

from engine.competitions.match_engine import CompetitionService
from engine.economy.sponsorships import SponsorshipService
from engine.economy.staff_market import StaffMarketService
from engine.social.stadium_fans import SocialService
from engine.world.time_and_finance import LogicalClock
from engine.world.weekly_cycle import WeeklyWorldCycleService
from test_staff_market_economy import make_db


def prepared_world(tmp_path):
    path = make_db(tmp_path)
    staff = StaffMarketService(path)
    staff.bootstrap_all_clubs()
    social = SocialService(staff.connection)
    social.create_stadium(1, "Casa", 20_000)
    social.create_stadium(2, "Fora", 10_000)
    social.ensure_fan_reputation(1, 18_000)
    social.ensure_fan_reputation(2, 8_000)
    sponsors = SponsorshipService(staff.connection)
    sponsors.bootstrap_all_clubs()
    competition = CompetitionService(staff.connection)
    season = competition.create_season(2026)
    competition_id = competition.create_competition("Semana", season, [1, 2])
    match_id = competition.generate_fixtures(competition_id)[0]
    staff.connection.execute("UPDATE matches SET match_date='2026-01-08' WHERE match_id=?", (match_id,))
    staff.connection.commit()
    return path, match_id


def test_weekly_cycle_processes_match_social_revenue_and_costs_once(tmp_path):
    path, match_id = prepared_world(tmp_path)
    service = WeeklyWorldCycleService(path)
    result = service.advance_week(seed=22)
    assert result["status"] == "COMPLETED"
    assert result["matches"] == 1
    assert service.connection.execute("SELECT status FROM matches WHERE match_id=?", (match_id,)).fetchone()[0] == "PLAYED"
    assert service.connection.execute("SELECT COUNT(*) FROM attendance_records WHERE match_id=?", (match_id,)).fetchone()[0] == 1
    categories = {row[0] for row in service.connection.execute("SELECT category FROM financial_ledger")}
    assert {"MATCHDAY", "PLAYER_PAYROLL", "STAFF_PAYROLL", "DEPARTMENT_MAINTENANCE"}.issubset(categories)
    event_types = {row[0] for row in service.connection.execute("SELECT type FROM club_events")}
    assert {"TORCIDA", "FINANCEIRO"}.issubset(event_types)
    clock = LogicalClock(service.connection).current()
    assert (clock["current_season"], clock["current_week"]) == (2026, 2)
    repeat = service.advance_week(seed=999)
    assert repeat["status"] == "COMPLETED"
    assert repeat["week"] == 3
    assert service.connection.execute("SELECT COUNT(*) FROM attendance_records WHERE match_id=?", (match_id,)).fetchone()[0] == 1


def test_explicit_week_is_idempotent_after_completion(tmp_path):
    path, _ = prepared_world(tmp_path)
    service = WeeklyWorldCycleService(path)

    first = service.process_week(2026, 2, seed=22)
    repeated = service.process_week(2026, 2, seed=999)

    assert first["status"] == "COMPLETED"
    assert repeated["status"] == "ALREADY_PROCESSED"
    assert repeated["tick_id"] == first["tick_id"]
    with pytest.raises(ValueError, match="WEEK_OUT_OF_SEQUENCE"):
        service.process_week(2026, 4, seed=22)


def test_weekly_cycle_rolls_back_clock_match_and_cash_on_ledger_failure(tmp_path):
    path, match_id = prepared_world(tmp_path)
    connection = sqlite3.connect(path)
    connection.execute("CREATE TRIGGER fail_matchday BEFORE INSERT ON financial_ledger WHEN NEW.category='MATCHDAY' BEGIN SELECT RAISE(ABORT, 'forced weekly failure'); END;")
    connection.commit()
    connection.close()
    service = WeeklyWorldCycleService(path)
    before_cash = service.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError, match="forced weekly failure"):
        service.advance_week(seed=22)
    assert LogicalClock(service.connection).current()["current_week"] == 1
    assert service.connection.execute("SELECT status FROM matches WHERE match_id=?", (match_id,)).fetchone()[0] == "SCHEDULED"
    assert service.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0] == before_cash
    assert service.connection.execute("SELECT status FROM weekly_world_runs WHERE season=2026 AND week=2").fetchone()[0] == "ROLLED_BACK"


def test_weekly_cycle_rolls_back_every_post_match_write_on_payroll_failure(tmp_path):
    path, match_id = prepared_world(tmp_path)
    connection = sqlite3.connect(path)
    connection.execute(
        """CREATE TRIGGER fail_player_payroll BEFORE INSERT ON financial_ledger
           WHEN NEW.category='PLAYER_PAYROLL'
           BEGIN SELECT RAISE(ABORT, 'forced post-match rollback'); END;"""
    )
    connection.commit()
    connection.close()

    service = WeeklyWorldCycleService(path)
    before_cash = service.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]

    with pytest.raises(sqlite3.IntegrityError, match="forced post-match rollback"):
        service.advance_week(seed=22)

    assert LogicalClock(service.connection).current()["current_week"] == 1
    assert service.connection.execute("SELECT status FROM matches WHERE match_id=?", (match_id,)).fetchone()[0] == "SCHEDULED"
    assert service.connection.execute("SELECT COUNT(*) FROM attendance_records WHERE match_id=?", (match_id,)).fetchone()[0] == 0
    assert service.connection.execute("SELECT COUNT(*) FROM club_social_history WHERE source_type='match' AND source_id=?", (str(match_id),)).fetchone()[0] == 0
    assert service.connection.execute("SELECT COUNT(*) FROM financial_ledger WHERE category='MATCHDAY'").fetchone()[0] == 0
    assert service.connection.execute("SELECT COUNT(*) FROM club_events").fetchone()[0] == 0
    assert service.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0] == before_cash
    assert service.connection.execute("SELECT status FROM weekly_world_runs WHERE season=2026 AND week=2").fetchone()[0] == "ROLLED_BACK"
