import shutil
import sqlite3
from pathlib import Path

from engine.manager.career import ManagerService

STATE = Path(__file__).parents[1] / "data/state/game.db"


def test_parallel_league_is_always_80_and_accepts_foreign_target(tmp_path):
    db = tmp_path / "game.db"
    shutil.copyfile(STATE, db)
    service = ManagerService(str(db))
    preview = service.preview_parallel_league([104, 65, 154], "club", 3280)
    assert preview["mode"] == "PARALLEL"
    assert preview["total_clubs"] == 80
    assert [len(item["clubs"]) for item in preview["divisions"]] == [20, 20, 20, 20]
    assert any(club["club_id"] == 3280 for division in preview["divisions"] for club in division["clubs"])


def test_single_country_preserves_national_flow(tmp_path):
    db = tmp_path / "game.db"
    shutil.copyfile(STATE, db)
    service = ManagerService(str(db))
    preview = service.preview_parallel_league([29], "club", 3280)
    assert preview["mode"] == "NATIONAL"
    assert preview["target_division"] == 4
    assert preview["preserved_national_competition"] is True


def test_sql_pool_uses_highest_institutional_overall(tmp_path):
    db = tmp_path / "game.db"
    shutil.copyfile(STATE, db)
    service = ManagerService(str(db))
    selected = service._eligible_clubs([97], "club", 0)
    assert len(selected) == 80
    scores = [service._club_overall(item["club_id"]) for item in selected]
    assert scores == sorted(scores, reverse=True)
    assert all(item["name"] and item["club_id"] for item in selected)


def test_catalog_exposes_named_supported_countries(tmp_path):
    db = tmp_path / "game.db"
    shutil.copyfile(STATE, db)
    service = ManagerService(str(db))
    countries = service.list_world_countries("", 48)
    by_id = {item["countryId"]: item for item in countries}
    assert {29, 104, 65, 154, 97, 3, 72, 11, 192} <= by_id.keys()
    assert all(not item["name"].startswith("País ID") for item in by_id.values())
    assert all(item["supported"] for item in by_id.values())
