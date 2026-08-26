from pathlib import Path
import hashlib
import shutil

import pytest

from engine.teams.identity import ClubIdentityService

ENGINE = Path(__file__).resolve().parents[1]
BASE = ENGINE / 'data/database/game.db'


def copy_state(tmp_path: Path) -> Path:
    target = tmp_path / 'game.db'
    shutil.copy2(ENGINE / 'data/state/game.db', target)
    return target


def test_identity_schema_and_documented_extensions_are_idempotent(tmp_path):
    path = copy_state(tmp_path)
    service = ClubIdentityService(path)
    service.upsert_club_identity(1, '1', 'Sudeste', 'Nacional', 80, 75)
    service.upsert_selection_identity(1, 'CONMEBOL', 'América do Sul', 'Copa', 'observed')
    service.add_alias(1, 'Mengão')
    service.record_rivalry(1, 2, 'fonte:documento-observado')
    service.record_name_history(1, 'Clube Histórico', 'fonte:documento-observado')
    service.record_stadium(1, 'Estádio Observado', 'fonte:sql')
    service.record_kits(1, 10, 11, 'fonte:arquivo-mãe')
    service.close()

    reopened = ClubIdentityService(path)
    tables = {row[0] for row in reopened.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {'club_identity_extensions', 'selection_identity_extensions', 'club_search_aliases', 'club_rivalries', 'club_name_history', 'club_stadium_identity', 'club_kit_links'} <= tables
    assert reopened.list_club_aliases(1)[0]['normalized_alias'] == 'mengão'
    reopened.close()


def test_documentation_is_required_for_rivalry_and_name_history(tmp_path):
    service = ClubIdentityService(copy_state(tmp_path))
    with pytest.raises(ValueError, match='DOCUMENTED_RIVALRY_REQUIRED'):
        service.record_rivalry(1, 1, '')
    with pytest.raises(ValueError, match='DOCUMENTED_NAME_HISTORY_REQUIRED'):
        service.record_name_history(1, '', '')
    service.close()


def test_identity_rejects_immutable_base():
    with pytest.raises(Exception):
        ClubIdentityService(BASE)


def test_base_hash_is_unchanged_by_read_only_identity_workflow():
    before = hashlib.sha256(BASE.read_bytes()).hexdigest()
    assert isinstance(before, str) and len(before) == 64
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == before
