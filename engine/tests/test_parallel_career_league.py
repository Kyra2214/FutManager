import shutil
import sqlite3
from pathlib import Path

import pytest

from engine.manager.career import ManagerService


STATE = Path(__file__).resolve().parents[1] / 'data/state/game.db'


@pytest.mark.parametrize(
    ('countries', 'expected_total'),
    [([29], 20), ([29, 104], 40), ([29, 104, 65], 60), ([29, 104, 65, 154], 78)],
)
def test_parallel_league_uses_all_official_first_division_clubs(tmp_path, countries, expected_total):
    db_path = tmp_path / 'game.db'
    shutil.copyfile(STATE, db_path)
    before = sqlite3.connect(db_path).execute('SELECT COUNT(*) FROM times').fetchone()[0]
    service = ManagerService(str(db_path))
    result = service.start_career('Manager Teste', 'BR', 30, 'Liga Paralela', 'club', 2009, selected_country_ids=countries)
    career_id = result['career_id']
    league = service.connection.execute('SELECT total_clubs,source_country_count,division_count,seed FROM career_parallel_leagues WHERE career_id=?', (career_id,)).fetchone()
    entries = service.connection.execute('SELECT club_id,parallel_division FROM career_parallel_entries WHERE career_id=?', (career_id,)).fetchall()
    after = sqlite3.connect(db_path).execute('SELECT COUNT(*) FROM times').fetchone()[0]

    if len(countries) == 1:
        reassignment = service.connection.execute('SELECT club_id,country_id,original_division,career_division FROM career_national_reassignments WHERE career_id=?', (career_id,)).fetchone()
        world_mode = service.connection.execute('SELECT world_mode FROM career_world_configs WHERE career_id=?', (career_id,)).fetchone()[0]
        assert league is None
        assert entries == []
        assert tuple(reassignment) == (2009, 29, 1, 4)
        assert world_mode == 'NATIONAL'
        assert result['parallel_league']['preserved_national_competition'] is True
    else:
        target_division = service.connection.execute('SELECT parallel_division FROM career_parallel_entries WHERE career_id=? AND club_id=2009', (career_id,)).fetchone()[0]
        assert tuple(league[:3]) == (expected_total, len(countries), 4)
        assert league[3]
        assert len(entries) == expected_total
        assert len({row[0] for row in entries}) == expected_total
        assert target_division == 4
        assert sum(1 for row in entries if row[1] == 1) + sum(1 for row in entries if row[1] == 2) + sum(1 for row in entries if row[1] == 3) + sum(1 for row in entries if row[1] == 4) == expected_total
    assert before == after


def test_parallel_league_generates_round_trip_calendar_and_closes_idempotently(tmp_path):
    db_path = tmp_path / 'game.db'
    shutil.copyfile(STATE, db_path)
    service = ManagerService(str(db_path))
    result = service.start_career('Manager Calendário', 'BR', 30, 'Temporada Paralela', 'club', 2009, selected_country_ids=[29, 104, 65, 154])
    career_id = result['career_id']
    snapshot = service.parallel_league_snapshot(career_id)

    assert snapshot['fixture_count'] == 1444
    assert snapshot['played_count'] == 0
    assert all(fixture['scheduled_date'] >= '2026-08-01' for fixture in snapshot['fixtures'])
    assert len(snapshot['standings']) == 78
    assert {row['division'] for row in snapshot['standings']} == {1, 2, 3, 4}

    closed = service.close_parallel_season(career_id)
    repeated = service.close_parallel_season(career_id)
    assert closed['status'] == 'CLOSED'
    assert closed['next_season'] == 2
    assert closed['next_fixtures'] == 1444
    assert repeated['status'] == 'ALREADY_CLOSED'
    assert service.parallel_league_snapshot(career_id, 2)['fixture_count'] == 1444


def test_single_country_uses_national_flow_and_main_country_names(tmp_path):
    db_path = tmp_path / 'game.db'
    shutil.copyfile(STATE, db_path)
    service = ManagerService(str(db_path))
    countries = service.list_world_countries(limit=48)
    names = {item['name'] for item in countries}
    assert {'Brasil', 'Itália', 'Espanha', 'Portugal', 'Inglaterra', 'Alemanha', 'França', 'Argentina', 'Turquia'} <= names
    result = service.start_career('Manager Nacional', 'BR', 30, 'Carreira Nacional', 'club', 2009, selected_country_ids=[29])
    career_id = result['career_id']
    assert result['world_mode'] == 'NATIONAL'
    assert result['parallel_league']['fixture_count'] == 0
    assert service.connection.execute('SELECT COUNT(*) FROM career_parallel_leagues WHERE career_id=?', (career_id,)).fetchone()[0] == 0
    assert service.connection.execute('SELECT career_division FROM career_national_reassignments WHERE career_id=?', (career_id,)).fetchone()[0] == 4


def test_constraint_audit_is_read_only_and_validates_parallel_state(tmp_path):
    db_path = tmp_path / 'game.db'
    shutil.copyfile(STATE, db_path)
    service = ManagerService(str(db_path))
    career_id = service.start_career('Manager Constraints', 'BR', 30, 'Constraints', 'club', 2009, selected_country_ids=[29, 104])['career_id']
    before = service.connection.execute('SELECT COUNT(*) FROM career_parallel_fixtures WHERE career_id=?', (career_id,)).fetchone()[0]
    audit = service.audit_constraints(career_id)
    after = service.connection.execute('SELECT COUNT(*) FROM career_parallel_fixtures WHERE career_id=?', (career_id,)).fetchone()[0]
    assert audit['status'] == 'VALID'
    assert all(audit['checks'].values())
    assert audit['violations'] == {'foreign_keys': [], 'duplicate_entries': [], 'duplicate_fixtures': [], 'invalid_divisions': []}
    assert before == after


def test_index_audit_confirms_calendar_and_standings_plans(tmp_path):
    db_path = tmp_path / 'game.db'
    shutil.copyfile(STATE, db_path)
    service = ManagerService(str(db_path))
    career_id = service.start_career('Manager Indexes', 'BR', 30, 'Indexes', 'club', 2009, selected_country_ids=[29, 104])['career_id']
    audit = service.audit_indexes(career_id)
    assert audit['status'] == 'VALID'
    assert all(audit['checks'].values())
    assert all(audit['indexes'].values())
    assert audit['plans']['fixtures']
    assert audit['plans']['standings']
