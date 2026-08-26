from pathlib import Path
import shutil
import sqlite3

import pytest

from engine.players.extensions import PlayerCanonicalExtensionService

ENGINE = Path(__file__).resolve().parents[1]
BASE = ENGINE / 'data/database/game.db'


def state_copy(tmp_path: Path) -> Path:
    target = tmp_path / 'game.db'
    shutil.copy2(ENGINE / 'data/state/game.db', target)
    return target


def test_extensions_are_created_idempotently_and_accept_observed_rows(tmp_path):
    path = state_copy(tmp_path)
    service = PlayerCanonicalExtensionService(path)
    service.upsert_position_alias(1, 'ME', 'Meia')
    service.record_progression(1, 2026, 22, 80)
    service.record_attributes(1, 2026, 70, 80, {'lado': 'D'})
    service.record_contract(1, 10, 2026, 1, 2027, 1, 1000, 50000, 'ACTIVE')
    service.record_profile(1, 'Meia', 'D', 60, {'temperamento': 'observado'})
    service.record_availability(1, 2026, 1, 'AVAILABLE')
    service.close()

    reopened = PlayerCanonicalExtensionService(path)
    tables = {row[0] for row in reopened.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {'player_position_aliases', 'player_progression', 'player_attribute_history', 'player_contract_history', 'player_profile_extensions', 'player_availability'} <= tables
    assert reopened.connection.execute('SELECT COUNT(*) FROM player_progression').fetchone()[0] == 1
    reopened.close()


def test_extensions_reject_invalid_observation_without_partial_write(tmp_path):
    path = state_copy(tmp_path)
    service = PlayerCanonicalExtensionService(path)
    with pytest.raises(ValueError, match='POSITION_ALIAS_REQUIRED'):
        service.upsert_position_alias(1, '', 'Meia')
    assert service.connection.execute('SELECT COUNT(*) FROM player_position_aliases').fetchone()[0] == 0
    service.close()


def test_read_reports_use_canonical_base_without_writing(tmp_path):
    original_hash = __import__('hashlib').sha256(BASE.read_bytes()).hexdigest()
    unattached = PlayerCanonicalExtensionService.unattached_players(BASE)
    incomplete = PlayerCanonicalExtensionService.incomplete_squads(BASE)
    assert isinstance(unattached, list)
    assert isinstance(incomplete, list)
    assert __import__('hashlib').sha256(BASE.read_bytes()).hexdigest() == original_hash


def test_mutable_extensions_reject_immutable_base():
    with pytest.raises(Exception):
        PlayerCanonicalExtensionService(BASE)
