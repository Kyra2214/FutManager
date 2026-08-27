import sqlite3

from engine.economy.world_economy import EconomyService
from engine.world.time_and_finance import LogicalClock
from engine.world.weekly_cycle import WeeklyWorldCycleService
from test_weekly_cycle import prepared_world


def test_full_season_uses_real_gamestate_with_checkpoint_and_finance_report(tmp_path):
    path, match_id = prepared_world(tmp_path)
    cycle = WeeklyWorldCycleService(path)

    results = [cycle.advance_week(seed=100 + week) for week in range(1, 13)]
    assert all(result["status"] == "COMPLETED" for result in results)
    assert LogicalClock(cycle.connection).current()["current_week"] == 13
    assert cycle.connection.execute("SELECT COUNT(*) FROM weekly_world_runs WHERE season=2026 AND status='COMPLETED'").fetchone()[0] == 12
    assert cycle.connection.execute("SELECT status FROM matches WHERE match_id=?", (match_id,)).fetchone()[0] == "PLAYED"
    assert cycle.connection.execute("SELECT COUNT(*) FROM attendance_records WHERE match_id=?", (match_id,)).fetchone()[0] == 1

    ledger_count = cycle.connection.execute("SELECT COUNT(*) FROM financial_ledger").fetchone()[0]
    assert ledger_count >= 12
    report = EconomyService(cycle.connection).audit_season(2026)
    assert report["season"] == 2026
    assert report["currency"] == "BRL"
    assert report["clubs"]
    assert report["clubs"][0]["club_id"] == 1
    assert report["clubs"][0]["by_category"]
    assert report["clubs"][0]["net"] != 0
    assert ledger_count >= len(report["clubs"][0]["by_category"])

    repeated = cycle.process_week(2026, 12, seed=999)
    assert repeated["status"] == "ALREADY_PROCESSED"
    assert repeated["tick_id"] == "weekly-world:2026:12"

    integrity = cycle.connection.execute("PRAGMA integrity_check").fetchone()[0]
    assert integrity == "ok"
    cycle.connection.close()
