from __future__ import annotations

import sqlite3

import pytest

from engine.core.schema import CURRENT_SCHEMA_VERSION
from engine.manager.career import ManagerService


def setup_service(tmp_path):
    db = tmp_path / 'state.sqlite'
    conn = sqlite3.connect(db)
    conn.execute('CREATE TABLE times(time_id INTEGER PRIMARY KEY, nome TEXT)')
    conn.execute('INSERT INTO times VALUES(1, "Clube A"),(2, "Clube B")')
    conn.commit()
    conn.close()
    return ManagerService(db)


def test_schema_v3_and_preferences_are_scoped(tmp_path):
    service = setup_service(tmp_path)
    manager = service.create_manager('Ana', 'BR', 30)
    service.set_preference(manager, 'density', 'compact')
    assert CURRENT_SCHEMA_VERSION == 3
    assert service.get_preferences(manager) == {'density': 'compact'}
    assert service.connection.execute('SELECT version FROM schema_versions WHERE component=?', ('game_state',)).fetchone()[0] == 3
    service.close()


def test_career_snapshot_close_and_resume(tmp_path):
    service = setup_service(tmp_path)
    manager = service.create_manager('Bia', 'BR', 28)
    career = service.create_career(manager, club_id=1, season_id=2026)
    snapshot = service.close_career(manager, 'teste de recuperação')
    assert snapshot > 0
    assert service.load(manager)['active_career'] == 0
    resumed = service.resume_career(manager, snapshot)
    assert resumed['career_id'] == career
    assert service.load(manager)['active_career'] == 1
    service.close()


def test_switch_club_is_idempotent_by_reference(tmp_path):
    service = setup_service(tmp_path)
    manager = service.create_manager('Caio', 'BR', 35)
    service.create_career(manager, club_id=1, season_id=2026)
    service.switch_club(manager, 2, 'change-1')
    service.switch_club(manager, 2, 'change-1')
    assert service.load(manager)['current_club_id'] == 2
    assert service.connection.execute('SELECT COUNT(*) FROM career_change_audit WHERE reference=?', ('change-1',)).fetchone()[0] == 1
    service.close()


def test_second_active_career_is_rejected(tmp_path):
    service = setup_service(tmp_path)
    manager = service.create_manager('Dani', 'BR', 25)
    service.create_career(manager, club_id=1)
    with pytest.raises(ValueError, match='ACTIVE_CAREER_EXISTS'):
        service.create_career(manager, club_id=2)
    service.close()
