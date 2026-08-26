import sqlite3
from datetime import date

from engine.competitions.match_engine import CompetitionService
from engine.economy.matchday_revenue import MatchdayRevenueService
from engine.social.stadium_fans import SocialService
from engine.world.time_and_finance import LogicalClock, WorldTickContext


def state():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    CompetitionService(connection)
    connection.execute("CREATE TABLE club_economic_state(club_id INTEGER PRIMARY KEY,cash INTEGER NOT NULL,updated_at TEXT)")
    connection.executemany("INSERT INTO club_economic_state VALUES(?,?,?)", [(1, 1_000_000, "2026-01-01"), (2, 1_000_000, "2026-01-01")])
    social = SocialService(connection)
    social.create_stadium(1, "Casa", 20_000)
    social.create_stadium(2, "Fora", 12_000)
    social.ensure_fan_reputation(1, 18_000)
    social.ensure_fan_reputation(2, 8_000)
    return connection


def context(connection):
    LogicalClock(connection)
    return WorldTickContext("test:2026:2", date(2026, 1, 8), 2026, 2, 1, "week", 19)


def test_matchday_credits_ledger_once_and_respects_played_match():
    connection = state()
    competition = CompetitionService(connection)
    season = competition.create_season(2026)
    cid = competition.create_competition("Teste", season, [1, 2])
    match_id = competition.generate_fixtures(cid)[0]
    competition.play(match_id, seed=4)
    service = MatchdayRevenueService(connection)
    before = connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    result = service.record_matchday(match_id, context(connection), importance=85)
    assert result["status"] == "PROCESSED"
    assert result["attendance"] <= 20_000
    assert connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0] == before + result["revenue"]
    assert service.record_matchday(match_id, context(connection))["status"] == "ALREADY_PROCESSED"
    assert connection.execute("SELECT COUNT(*) FROM financial_ledger WHERE category='MATCHDAY'").fetchone()[0] == 1


def test_competition_prize_uses_final_standing_and_is_idempotent():
    connection = state()
    competition = CompetitionService(connection)
    season = competition.create_season(2026)
    cid = competition.create_competition("Teste", season, [1, 2])
    match_id = competition.generate_fixtures(cid)[0]
    competition.play(match_id, seed=8)
    service = MatchdayRevenueService(connection)
    service.configure_prize(cid, 1, 500_000)
    service.configure_prize(cid, 2, 120_000)
    result = service.award_completed_competition(cid, context(connection))
    assert result["status"] == "PROCESSED"
    assert len(result["awards"]) == 2
    assert service.award_completed_competition(cid, context(connection))["status"] == "ALREADY_PROCESSED"
    assert connection.execute("SELECT COUNT(*) FROM financial_ledger WHERE category='COMPETITION_PRIZE'").fetchone()[0] == 2
