from engine.economy.sponsorships import OFFER_WINDOW_WEEKS, SponsorshipService
from engine.economy.staff_market import StaffMarketService
from engine.competitions.match_engine import CompetitionService
from engine.economy.matchday_revenue import MatchdayRevenueService
from engine.social.stadium_fans import SocialService
from engine.world.time_and_finance import LogicalClock, WorldTickContext
from datetime import date
from test_staff_market_economy import make_db


def test_offers_expire_and_rotate_with_institutional_stars(tmp_path):
    path = make_db(tmp_path)
    StaffMarketService(path).bootstrap_all_clubs()
    service = SponsorshipService(path)
    initial = service.bootstrap_club(1)
    assert len(initial["offers"]) == 3
    assert 1 <= initial["sponsor_stars"] <= 5
    assert all(1 <= offer["star_rating"] <= initial["sponsor_stars"] for offer in initial["offers"])
    first_offer_ids = {offer["offer_id"] for offer in initial["offers"]}
    service.connection.execute("UPDATE logical_clock SET current_week=? WHERE clock_id=1", (1 + OFFER_WINDOW_WEEKS,))
    processed = service.process_week(1)
    rotated = service.offers(1)
    assert processed["processed"] is True
    assert len(rotated) == 3
    assert first_offer_ids.isdisjoint({offer["offer_id"] for offer in rotated})
    service.close()


def test_acceptance_pays_upfront_and_weekly_income_is_idempotent(tmp_path):
    path = make_db(tmp_path)
    StaffMarketService(path).bootstrap_all_clubs()
    service = SponsorshipService(path)
    offer = service.bootstrap_club(1)["offers"][0]
    before = service.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    contract = service.accept_offer(1, offer["offer_id"])
    after_accept = service.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    assert after_accept - before == contract["upfront_payment"]
    first_week = service.process_week(1)
    after_week = service.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    assert after_week - after_accept == contract["weekly_payment"] + sum(first_week["mission_rewards"])
    assert service.process_week(1)["reason"] == "ALREADY_PROCESSED"
    service.close()


def test_completed_mission_pays_once(tmp_path):
    path = make_db(tmp_path)
    StaffMarketService(path).bootstrap_all_clubs()
    service = SponsorshipService(path)
    offer = service.bootstrap_club(1)["offers"][0]
    service.accept_offer(1, offer["offer_id"])
    mission = service.connection.execute("SELECT mission_id,reward FROM sponsor_missions WHERE club_id=1").fetchone()
    service.connection.execute("UPDATE sponsor_missions SET target_value=0 WHERE mission_id=?", (mission["mission_id"],))
    before = service.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    result = service.process_week(1)
    after = service.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    assert mission["reward"] in result["mission_rewards"]
    assert after - before == result["weekly_income"] + mission["reward"]
    service.close()


def test_offer_window_crosses_to_the_next_season_without_week_zero(tmp_path):
    path = make_db(tmp_path)
    StaffMarketService(path).bootstrap_all_clubs()
    service = SponsorshipService(path)
    service.connection.execute("UPDATE logical_clock SET current_season=2026,current_week=52 WHERE clock_id=1")
    offers = service.bootstrap_club(1)["offers"]
    assert {offer["expires_season"] for offer in offers} == {2027}
    assert {offer["expires_week"] for offer in offers} == {2}
    service.close()


def test_match_mission_uses_persisted_match_and_matchday_once(tmp_path):
    path = make_db(tmp_path)
    StaffMarketService(path).bootstrap_all_clubs()
    service = SponsorshipService(path)
    social = SocialService(service.connection)
    social.create_stadium(1, "Casa", 20_000)
    social.create_stadium(2, "Fora", 10_000)
    social.ensure_fan_reputation(1, 18_000)
    social.ensure_fan_reputation(2, 9_000)
    competitions = CompetitionService(service.connection)
    season = competitions.create_season(2026)
    competition_id = competitions.create_competition("Teste", season, [1, 2])
    match_id = competitions.generate_fixtures(competition_id)[0]
    competitions.play(match_id, home_strength=100, away_strength=1, seed=14)
    service.connection.execute("UPDATE matches SET home_goals=2,away_goals=0,status='PLAYED' WHERE match_id=?", (match_id,))
    clock = LogicalClock(service.connection)
    tick = WorldTickContext("test:match", date(2026, 1, 8), 2026, 2, 1, "week", 9)
    MatchdayRevenueService(service.connection).record_matchday(match_id, tick)
    offer = service.bootstrap_club(1)["offers"][0]
    service.accept_offer(1, offer["offer_id"])
    mission = service.connection.execute("SELECT mission_id,reward FROM sponsor_missions WHERE club_id=1").fetchone()
    service.connection.execute("UPDATE sponsor_missions SET mission_type='match_wins',target_value=1,current_value=0 WHERE mission_id=?", (mission["mission_id"],))
    before = service.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    first = service.record_match_progress_from_state(match_id, tick)
    after = service.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    assert first["home"]["updated"] == 1
    assert after - before == mission["reward"]
    assert service.record_match_progress_from_state(match_id, tick)["home"]["updated"] == 0
    assert service.connection.execute("SELECT COUNT(*) FROM financial_ledger WHERE category='SPONSOR_MISSION'").fetchone()[0] == 1
    service.close()


def test_match_mission_rejects_missing_or_not_played_match(tmp_path):
    service = SponsorshipService(make_db(tmp_path))
    import pytest
    with pytest.raises(ValueError, match="MATCH_NOT_FOUND"):
        service.record_match_progress_from_state(999)
    competitions = CompetitionService(service.connection)
    season = competitions.create_season(2026)
    competition_id = competitions.create_competition("Teste", season, [1, 2])
    match_id = competitions.generate_fixtures(competition_id)[0]
    with pytest.raises(ValueError, match="MATCH_NOT_PLAYED"):
        service.record_match_progress_from_state(match_id)
    service.close()
