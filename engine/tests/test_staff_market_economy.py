import sqlite3

import pytest

from engine.economy.staff_market import FORMULA_VERSION, INITIAL_RESERVE_WEEKS, StaffMarketService


def make_db(tmp_path):
    path = tmp_path / "staff_market.db"
    con = sqlite3.connect(path)
    con.executescript("""
      CREATE TABLE times(time_id INTEGER PRIMARY KEY,nome TEXT,pais_id INTEGER);
      CREATE TABLE jogadores(jogador_id INTEGER PRIMARY KEY,cr1 INTEGER,cr2 INTEGER,estrela INTEGER,top_mundial INTEGER,idade INTEGER,posicao TEXT);
      CREATE TABLE jogador_time(jogador_id INTEGER,time_id INTEGER,status TEXT);
      CREATE TABLE staff_members(staff_id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,role TEXT,age INTEGER,club_id INTEGER,career_start_age INTEGER,experience INTEGER,reputation INTEGER,level INTEGER,potential INTEGER,specialization TEXT,salary INTEGER,contract_id INTEGER,status TEXT,created_at TEXT,retirement_age INTEGER);
      CREATE TABLE staff_history(history_id INTEGER PRIMARY KEY AUTOINCREMENT,staff_id INTEGER,event_type TEXT,event_date TEXT,payload TEXT);
      CREATE TABLE club_departments(club_id INTEGER,department TEXT,level INTEGER,cost INTEGER,capacity INTEGER,maintenance INTEGER,efficiency REAL,PRIMARY KEY(club_id,department));
    """)
    con.execute("INSERT INTO times VALUES(1,'Clube A',1)")
    con.execute("INSERT INTO times VALUES(2,'Clube B',1)")
    for player_id, team_id, status, cr1, cr2, star, age, position in [(1,1,'Titular',8,9,1,27,'Atacante'),(2,1,'Titular',8,8,0,34,'Goleiro'),(3,2,'Titular',7,7,0,25,'Meia')]:
        con.execute("INSERT INTO jogadores VALUES(?,?,?,?,0,?,?)",(player_id,cr1,cr2,star,age,position))
        con.execute("INSERT INTO jogador_time VALUES(?,?,?)",(player_id,team_id,status))
    con.commit(); con.close()
    return path


def test_initial_cash_contracts_staff_and_department_weekly_costs(tmp_path):
    service = StaffMarketService(make_db(tmp_path))
    profile = service.ensure_club_economy(1)
    assert profile.initial_cash == profile.weekly_player_payroll * INITIAL_RESERVE_WEEKS
    player_rows = service.connection.execute("SELECT formula_version,player_strength,weekly_salary FROM club_player_payrolls WHERE club_id=1 ORDER BY player_id").fetchall()
    assert len(player_rows) == 2
    assert all(row["formula_version"] == FORMULA_VERSION and row["player_strength"] > 0 and row["weekly_salary"] >= 500 for row in player_rows)
    offers = service.available_staff(1, "medico")
    assert offers and offers[0]["weekly_salary"] > 0
    hired = service.hire_staff(1, offers[0]["staff_id"])
    assert hired["weekly_salary"] > 0
    department = service.upgrade_department(1, "medicina")
    assert department["target_level"] == 1
    before = service.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    weekly = service.process_weekly_costs(1)
    after = service.connection.execute("SELECT cash FROM club_economic_state WHERE club_id=1").fetchone()[0]
    assert weekly["processed"] is True and before - after == weekly["weekly_cost"]
    assert service.process_weekly_costs(1)["reason"] == "ALREADY_PROCESSED"
    service.close()


def test_economy_bootstrap_creates_staff_schema_when_it_is_absent(tmp_path):
    path = tmp_path / "economy_without_staff_schema.db"
    con = sqlite3.connect(path)
    con.executescript("""
      CREATE TABLE times(time_id INTEGER PRIMARY KEY,nome TEXT,pais_id INTEGER);
      CREATE TABLE jogadores(jogador_id INTEGER PRIMARY KEY,cr1 INTEGER,cr2 INTEGER,estrela INTEGER,top_mundial INTEGER,idade INTEGER,posicao TEXT);
      CREATE TABLE jogador_time(jogador_id INTEGER,time_id INTEGER,status TEXT);
      INSERT INTO times VALUES(1,'Clube A',29);
      INSERT INTO jogadores VALUES(1,9,8,0,0,26,'Meia');
      INSERT INTO jogador_time VALUES(1,1,'Titular');
    """)
    con.commit(); con.close()
    service = StaffMarketService(path)
    profile = service.ensure_club_economy(1)
    tables = {row[0] for row in service.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"staff_members", "staff_history", "club_departments", "club_player_payrolls"}.issubset(tables)
    assert profile.initial_cash == profile.weekly_player_payroll * INITIAL_RESERVE_WEEKS
    service.close()


def test_world_bootstrap_is_explicit_and_idempotent(tmp_path):
    service = StaffMarketService(make_db(tmp_path))
    first = service.bootstrap_all_clubs()
    assert first["clubs_total"] == 2
    assert first["created"] == 2
    assert first["skipped"] == 0
    assert first["formula_version"] == FORMULA_VERSION
    second = service.bootstrap_all_clubs()
    assert second["created"] == 0
    assert second["skipped"] == 2
    service.close()


def test_hiring_rolls_back_when_history_cannot_be_recorded(tmp_path):
    service = StaffMarketService(make_db(tmp_path))
    profile = service.ensure_club_economy(1)
    staff = service.available_staff(1, "medico")[0]
    service.connection.execute("""CREATE TRIGGER fail_hire_history BEFORE INSERT ON staff_history
        WHEN NEW.event_type='STAFF_HIRED' BEGIN SELECT RAISE(ABORT, 'forced hire rollback'); END;""")
    with pytest.raises(sqlite3.IntegrityError):
        service.hire_staff(1, staff["staff_id"])
    member = service.connection.execute("SELECT club_id,status,salary FROM staff_members WHERE staff_id=?", (staff["staff_id"],)).fetchone()
    state = service.connection.execute("SELECT payroll FROM club_economic_state WHERE club_id=1").fetchone()
    assert member["club_id"] is None and member["status"] == "disponivel" and member["salary"] == 0
    assert state["payroll"] == profile.weekly_player_payroll
    service.close()


def test_world_weekly_processing_is_idempotent(tmp_path):
    service = StaffMarketService(make_db(tmp_path))
    service.bootstrap_all_clubs()
    first = service.process_weekly_costs_all()
    assert first["clubs_total"] == 2
    assert first["processed"] == 2
    assert not first["insufficient_cash_club_ids"]
    second = service.process_weekly_costs_all()
    assert second["processed"] == 0
    assert second["already_processed"] == 2
    service.close()


def test_summary_is_read_only_after_bootstrap(tmp_path):
    service = StaffMarketService(make_db(tmp_path))
    service.bootstrap_club(1)
    before = service.connection.total_changes
    summary = service.summary(1)
    assert summary["club_id"] == 1
    assert service.connection.total_changes == before
    service.close()


def test_staff_contract_lifecycle_and_replacement(tmp_path):
    service=StaffMarketService(make_db(tmp_path))
    service.ensure_club_economy(1)
    available=service.available_staff(1,'medico')
    first=service.hire_staff(1,available[0]['staff_id'])
    contract=service.staff_contract(1,first['staff_id'])
    assert contract['status'] == 'ACTIVE' and contract['weekly_salary'] == first['weekly_salary']
    assert contract['end_date'] > contract['start_date'] and contract['termination_fee'] == first['weekly_salary'] * 4
    second=service.available_staff(1,'medico')[0]
    replacement=service.replace_staff(1,first['staff_id'],second['staff_id'])
    assert replacement['terminated']['status'] == 'disponivel' and replacement['hired']['staff_id'] == second['staff_id']
    assert service.connection.execute("SELECT COUNT(*) FROM staff_members WHERE club_id=1 AND status='ativo'").fetchone()[0] == 1
    assert service.connection.execute("SELECT COUNT(*) FROM staff_contracts WHERE club_id=1 AND status='ACTIVE'").fetchone()[0] == 1
    service.close()


def test_staff_catalog_covers_canonical_roles_and_attribute_ranges(tmp_path):
    service=StaffMarketService(make_db(tmp_path))
    service.seed_catalog()
    rows=service.connection.execute("SELECT role,level,experience,reputation,potential FROM staff_members WHERE status='disponivel'").fetchall()
    assert {row['role'] for row in rows} == {'treinador','auxiliar','preparador_fisico','medico','scout'}
    assert all(1 <= row['level'] <= 10 and 0 <= row['experience'] <= 100 and 1 <= row['reputation'] <= 100 and 30 <= row['potential'] <= 99 for row in rows)
    assert len(rows) == 10
    service.close()


def test_staff_catalog_filters_levels_and_exposes_cost_benefit(tmp_path):
    service=StaffMarketService(make_db(tmp_path))
    rows=service.available_staff(1, 'medico', min_level=6, max_level=8)
    assert rows and all(6 <= row['level'] <= 8 for row in rows)
    assert all(row['cost_benefit'] > 0 for row in rows)
    assert rows == sorted(rows, key=lambda item: (-item['cost_benefit'], -item['level'], -item['reputation'], item['name']))
    assert all(row['specialization'] for row in service.available_staff(1, 'auxiliar'))
    service.close()
