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


def test_backup_manifest_is_deterministic_and_idempotent(tmp_path):
    db_path = tmp_path / 'game.db'
    shutil.copyfile(STATE, db_path)
    service = ManagerService(str(db_path))
    career_id = service.start_career('Manager Backup', 'BR', 30, 'Backup', 'club', 2009, selected_country_ids=[29, 104])['career_id']
    first = service.create_backup_manifest(career_id)
    repeated = service.create_backup_manifest(career_id)
    manifests = service.list_backup_manifests(career_id)
    assert first['state_hash'] == repeated['state_hash']
    assert first['backup_id'] == repeated['backup_id']
    assert first['status'] == 'VERIFIED'
    assert first['row_counts']['career_parallel_fixtures'] == 360
    assert len(manifests) == 1


def test_snapshot_audit_confirms_scope_and_hashes(tmp_path):
    db_path = tmp_path / 'game.db'
    shutil.copyfile(STATE, db_path)
    service = ManagerService(str(db_path))
    career_id = service.start_career('Manager Snapshot Audit', 'BR', 30, 'Snapshot Audit', 'club', 2009, selected_country_ids=[29])['career_id']
    snapshot_id = service.snapshot(career_id)
    audit = service.audit_snapshots(career_id)
    assert snapshot_id > 0
    assert audit['status'] == 'VALID'
    assert audit['snapshot_count'] == 1
    assert all(audit['checks'].values())
    assert audit['read_only'] is True


def test_restore_preview_is_read_only_and_reports_field_diff(tmp_path):
    db_path = tmp_path / 'game.db'
    shutil.copyfile(STATE, db_path)
    service = ManagerService(str(db_path))
    started = service.start_career('Manager Restore Preview', 'BR', 30, 'Restore Preview', 'club', 2009, selected_country_ids=[29])
    career_id = started['career_id']
    manager_id = started['manager_id']
    snapshot_id = service.snapshot(career_id)
    preview = service.preview_restore(manager_id, snapshot_id, ['current_club_id', 'status'])
    assert preview['read_only'] is True
    assert preview['career_id'] == career_id
    assert {change['field'] for change in preview['changes']} == {'current_club_id', 'status'}
    assert service.connection.execute('SELECT COUNT(*) FROM career_snapshot_audit WHERE career_id=?', (career_id,)).fetchone()[0] == 0


def test_journal_is_sequenced_scoped_and_idempotent(tmp_path):
    db_path = tmp_path / 'game.db'
    shutil.copyfile(STATE, db_path)
    service = ManagerService(str(db_path))
    started = service.start_career('Manager Journal', 'BR', 30, 'Journal', 'club', 2009, selected_country_ids=[29])
    career_id, manager_id = started['career_id'], started['manager_id']
    first = service.append_journal(career_id, manager_id, 'CAREER_STARTED', 'career', career_id, {'source': 'test'})
    repeated = service.append_journal(career_id, manager_id, 'CAREER_STARTED', 'career', career_id, {'source': 'test'})
    second = service.append_journal(career_id, manager_id, 'SNAPSHOT_CREATED', 'snapshot', 1, {'source': 'test'})
    rows = service.list_journal(career_id)
    audit = service.audit_journal(career_id)
    assert first['sequence_no'] == 1
    assert repeated['journal_id'] == first['journal_id']
    assert repeated['idempotent'] is True
    assert second['sequence_no'] == 2
    assert [row['sequence_no'] for row in rows] == [1, 2]
    assert audit['status'] == 'VALID'
    assert all(audit['checks'].values())
    assert audit['read_only'] is True
