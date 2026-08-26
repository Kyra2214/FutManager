from datetime import date
import sqlite3

from engine.economy.travel_costs import TravelCostService
from engine.world.time_and_finance import FinanceLedger, LogicalClock, WorldTickContext


def database():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE times(time_id INTEGER PRIMARY KEY, pais_id INTEGER);
        CREATE TABLE matches(match_id INTEGER PRIMARY KEY, home_club_id INTEGER, away_club_id INTEGER);
        CREATE TABLE club_economic_state(club_id INTEGER PRIMARY KEY, cash INTEGER NOT NULL, updated_at TEXT NOT NULL, financial_status TEXT NOT NULL DEFAULT 'HEALTHY');
        """
    )
    LogicalClock(connection, start_date=date(2026, 1, 1), season=2026)
    connection.executemany("INSERT INTO times(time_id,pais_id) VALUES(?,?)", [(1, 29), (2, 29), (3, 30)])
    connection.executemany("INSERT INTO matches(match_id,home_club_id,away_club_id) VALUES(?,?,?)", [(10, 1, 2), (11, 1, 3)])
    connection.executemany("INSERT INTO club_economic_state(club_id,cash,updated_at) VALUES(?,?,?)", [(1, 1_000_000, '2026-01-01'), (2, 1_000_000, '2026-01-01'), (3, 1_000_000, '2026-01-01')])
    connection.commit()
    return connection


def context():
    return WorldTickContext("travel:2026:2", date(2026, 1, 8), 2026, 2, 1, "week", 7)


def test_preview_is_read_only_and_distinguishes_routes():
    connection = database()
    service = TravelCostService(connection)

    domestic = service.preview(10, 2)
    international = service.preview(11, 3)

    assert domestic == {
        "status": "AVAILABLE", "match_id": 10, "club_id": 2, "opponent_id": 1,
        "route_type": "DOMESTIC", "cost": 25_000, "currency": "BRL", "reason": None, "persisted": False,
    }
    assert international["route_type"] == "INTERNATIONAL"
    assert international["cost"] == 100_000
    assert connection.execute("SELECT COUNT(*) FROM financial_ledger").fetchone()[0] == 0
    assert connection.execute("SELECT cash FROM club_economic_state WHERE club_id=2").fetchone()[0] == 1_000_000


def test_post_is_idempotent_and_debits_visitor_cash():
    connection = database()
    service = TravelCostService(connection)

    first = service.post_for_match(10, context())
    second = service.post_for_match(10, context())

    assert first["status"] == "PROCESSED"
    assert second["status"] == "ALREADY_PROCESSED"
    assert connection.execute("SELECT COUNT(*) FROM financial_ledger WHERE category='TRAVEL'").fetchone()[0] == 1
    assert connection.execute("SELECT amount FROM financial_ledger WHERE category='TRAVEL'").fetchone()[0] == -25_000
    assert connection.execute("SELECT cash FROM club_economic_state WHERE club_id=2").fetchone()[0] == 975_000


def test_home_club_has_no_travel_expense():
    connection = database()
    service = TravelCostService(connection)
    result = service.post_for_match(10, context())

    assert result["club_id"] == 2
    assert service.preview(10, 1)["route_type"] == "HOME_NO_TRAVEL"
    assert FinanceLedger.CURRENCY == "BRL"
