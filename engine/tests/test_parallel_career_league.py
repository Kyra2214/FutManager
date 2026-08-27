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
    after = service.connection.execute('SELECT COUNT(*) FROM times').fetchone()[0]
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
