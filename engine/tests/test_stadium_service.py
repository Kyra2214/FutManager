import sqlite3

import pytest

from engine.economy.staff_market import StaffMarketService
from engine.stadiums.service import MAX_LEVEL, StadiumService


def create_state():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE times(time_id INTEGER PRIMARY KEY, pais_id INTEGER, estadio TEXT)")
    connection.execute("CREATE TABLE jogador_time(jogador_id INTEGER,time_id INTEGER,status TEXT,atual INTEGER)")
    connection.execute("CREATE TABLE jogadores(jogador_id INTEGER PRIMARY KEY, cr1 INTEGER, cr2 INTEGER, idade INTEGER, posicao TEXT, estrela INTEGER, top_mundial INTEGER)")
    connection.execute("INSERT INTO times VALUES(1,1,'Estádio de Teste')")
    for player_id in range(1, 12):
        connection.execute("INSERT INTO jogadores VALUES(?,?,?,?,?,?,?)", (player_id, 8, 8, 25, "MC", 0, 0))
        connection.execute("INSERT INTO jogador_time VALUES(?,?,?,?)", (player_id, 1, "Titular", 1))
    connection.commit()
    StaffMarketService(connection).ensure_club_economy(1)
    return connection


def test_bootstrap_stadium_has_four_components_and_level_one():
    connection = create_state()
    service = StadiumService(connection)
    state = service.bootstrap_club(1)
    assert state["name"] == "Estádio de Teste"
    assert state["capacity"] == 12_000
    assert {component["component"] for component in state["components"]} == {"arquibancada", "campo", "estrutura", "equipes"}
    assert {component["level"] for component in state["components"]} == {1}


def test_upgrade_charges_ledger_and_updates_capacity_once():
    connection = create_state()
    service = StadiumService(connection)
    service.bootstrap_club(1)
    before = connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    result = service.upgrade_stadium_component(1, "arquibancada")
    after = connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    assert result["target_level"] == 2
    assert after == before - result["cost"]
    assert result["stadium"]["capacity"] == 14_250
    assert connection.execute("SELECT COUNT(*) FROM financial_ledger WHERE category='STADIUM_UPGRADE'").fetchone()[0] == 1
    with pytest.raises(ValueError, match="ALREADY_PROCESSED"):
        connection.execute("UPDATE stadium_components SET level=1 WHERE stadium_id=1 AND component='arquibancada'")
        service.upgrade_stadium_component(1, "arquibancada")


def test_level_ten_blocks_an_upgrade_without_partial_charge():
    connection = create_state()
    service = StadiumService(connection)
    service.bootstrap_club(1)
    connection.execute("UPDATE stadium_components SET level=? WHERE stadium_id=1 AND component='campo'", (MAX_LEVEL,))
    before = connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    with pytest.raises(ValueError, match="STADIUM_COMPONENT_MAX_LEVEL"):
        service.upgrade_stadium_component(1, "campo")
    assert connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0] == before


def test_bootstrap_reconciles_existing_social_stadium_with_components():
    connection = create_state()
    connection.execute(
        """CREATE TABLE club_stadiums(stadium_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER,name TEXT,capacity INTEGER,usable_capacity INTEGER,state INTEGER,level INTEGER,comfort INTEGER,security INTEGER,quality INTEGER,maintenance_cost INTEGER,construction_date TEXT,last_maintenance TEXT,status TEXT,is_primary INTEGER)"""
    )
    connection.execute("INSERT INTO club_stadiums VALUES(1,1,'Legado',30000,30000,100,3,40,40,40,4000,'2026-01-01','2026-01-01','ACTIVE',1)")
    connection.commit()
    state = StadiumService(connection).bootstrap_club(1)
    assert state["stadium_id"] == 1
    assert {component["level"] for component in state["components"]} == {3}
    assert state["capacity"] == 34_500


def test_successive_upgrades_reach_level_ten_and_rollback_after_ledger_error():
    connection = create_state()
    service = StadiumService(connection)
    service.bootstrap_club(1)
    connection.execute("UPDATE club_economic_state SET cash=10000000 WHERE club_id=1")
    connection.commit()
    for _ in range(9):
        result = service.upgrade_stadium_component(1, "campo")
    assert result["target_level"] == 10
    reference = "stadium:1:estrutura:2"
    connection.execute("INSERT INTO stadium_component_history(stadium_id,component,from_level,to_level,cost,maintenance_after,event_date,reference) VALUES(1,'estrutura',1,2,0,0,'2026-01-01',?)", (reference,))
    before_cash = connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    with pytest.raises(sqlite3.IntegrityError):
        service.upgrade_stadium_component(1, "estrutura")
    assert connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0] == before_cash
    assert connection.execute("SELECT COUNT(*) FROM financial_ledger WHERE source_id=?", (reference,)).fetchone()[0] == 0


def test_world_bootstrap_creates_only_source_backed_stadiums_and_is_idempotent():
    connection = create_state()
    connection.execute("INSERT INTO times VALUES(2,1,'Segundo Estádio')")
    connection.execute("INSERT INTO times VALUES(3,1,NULL)")
    connection.commit()
    service = StadiumService(connection)
    first = service.bootstrap_all_clubs()
    assert first == {"clubs_total": 2, "created": 2, "reconciled": 0, "skipped": 0}
    assert connection.execute("SELECT COUNT(*) FROM stadium_components").fetchone()[0] == 8
    second = service.bootstrap_all_clubs()
    assert second["created"] == 0 and second["skipped"] == 2
