from engine.economy.sponsorships import SponsorshipService
from engine.economy.staff_market import StaffMarketService
from engine.economy.world_economy import WorldEconomyService
from test_staff_market_economy import make_db


def test_world_week_combines_sponsorship_income_and_payroll_idempotently(tmp_path):
    path = make_db(tmp_path)
    StaffMarketService(path).bootstrap_all_clubs()
    sponsors = SponsorshipService(path)
    offer = sponsors.bootstrap_club(1)["offers"][0]
    sponsors.bootstrap_club(2)
    contract = sponsors.accept_offer(1, offer["offer_id"])
    connection = sponsors.connection
    before = connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    payroll = connection.execute("SELECT weekly_player_payroll FROM club_payroll_profiles WHERE club_id=1").fetchone()[0]
    world = WorldEconomyService(connection)
    result = world.process_world_week()
    after = connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    assert result["clubs_total"] == 2
    assert result["sponsorship_processed"] == 2
    assert result["payroll_processed"] == 2
    assert after - before == contract["weekly_payment"] - payroll
    repeated = world.process_world_week()
    assert repeated["sponsorship_processed"] == 0
    assert repeated["payroll_processed"] == 0
    world.close()
