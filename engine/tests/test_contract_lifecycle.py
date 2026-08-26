import sqlite3

import pytest

from engine.players.contracts import PlayerContractService
from engine.world.time_and_finance import LogicalClock


def make_state(path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    LogicalClock(connection)
    connection.executescript(
        """
        CREATE TABLE player_contract_history (
            contract_id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER, club_id INTEGER, start_season INTEGER,
            start_week INTEGER, end_season INTEGER, end_week INTEGER,
            weekly_salary INTEGER, release_clause INTEGER, status TEXT, source TEXT
        );
        CREATE TABLE club_ai_profiles (club_id INTEGER PRIMARY KEY, salary_limit INTEGER, strategy TEXT);
        CREATE TABLE club_payroll_profiles (club_id INTEGER PRIMARY KEY, weekly_player_payroll INTEGER);
        INSERT INTO player_contract_history VALUES (1, 7, 1, 2026, 1, 2026, 5, 1000, 50000, 'ACTIVE', 'seed');
        INSERT INTO club_ai_profiles VALUES (1, 3000, 'balanced');
        INSERT INTO club_payroll_profiles VALUES (1, 2000);
        """
    )
    connection.commit()
    connection.close()


def test_renewal_requires_explicit_manager_approval(tmp_path):
    path = tmp_path / "game.db"
    make_state(path)
    service = PlayerContractService(path)
    try:
        with pytest.raises(ValueError, match="MANAGER_APPROVAL_REQUIRED"):
            service.approve_renewal(player_id=7, club_id=1, season=2026, week=2, weekly_salary=1200)
    finally:
        service.close()
    connection = sqlite3.connect(path)
    assert connection.execute("SELECT status FROM player_contract_history").fetchone()[0] == "ACTIVE"
    assert connection.execute("SELECT COUNT(*) FROM financial_ledger").fetchone()[0] == 0
    connection.close()


def test_renewal_posts_accessory_costs_and_updates_payroll_atomically(tmp_path):
    path = tmp_path / "game.db"
    make_state(path)
    service = PlayerContractService(path)
    try:
        result = service.approve_renewal(player_id=7, club_id=1, season=2026, week=2, weekly_salary=1200, signing_fee=500, bonus=250, manager_approved=True)
        assert result["status"] == "APPROVED"
    finally:
        service.close()
    connection = sqlite3.connect(path)
    assert connection.execute("SELECT status FROM player_contract_history WHERE contract_id=1").fetchone()[0] == "REPLACED"
    assert connection.execute("SELECT COUNT(*) FROM player_contract_history WHERE status='ACTIVE'").fetchone()[0] == 1
    assert connection.execute("SELECT weekly_player_payroll FROM club_payroll_profiles WHERE club_id=1").fetchone()[0] == 2200
    assert connection.execute("SELECT SUM(amount) FROM financial_ledger WHERE club_id=1").fetchone()[0] == -750
    connection.close()


def test_salary_cap_rejection_rolls_back_contract_and_ledger(tmp_path):
    path = tmp_path / "game.db"
    make_state(path)
    service = PlayerContractService(path)
    try:
        with pytest.raises(ValueError, match="SALARY_CAP_EXCEEDED"):
            service.approve_renewal(player_id=7, club_id=1, season=2026, week=2, weekly_salary=2001, signing_fee=100, manager_approved=True)
    finally:
        service.close()
    connection = sqlite3.connect(path)
    assert connection.execute("SELECT status FROM player_contract_history WHERE contract_id=1").fetchone()[0] == "ACTIVE"
    assert connection.execute("SELECT COUNT(*) FROM player_contract_history").fetchone()[0] == 1
    assert connection.execute("SELECT weekly_player_payroll FROM club_payroll_profiles WHERE club_id=1").fetchone()[0] == 2000
    assert connection.execute("SELECT COUNT(*) FROM financial_ledger").fetchone()[0] == 0
    connection.close()
