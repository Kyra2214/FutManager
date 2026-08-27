import sqlite3
from pathlib import Path

from engine.manager.career import ManagerService
from engine.world.first_division import FIRST_DIVISION_SOURCES, resolve_first_division_members

STATE = Path(__file__).resolve().parents[1] / "data/state/game.db"


def test_new_official_memberships_match_canonical_sql():
    connection = sqlite3.connect(STATE)
    try:
        for country_id in (3, 72):
            report = resolve_first_division_members(connection, country_id)
            assert report["unmatched"] == []
            assert report["ambiguous"] == []
            assert len(report["matched"]) == report["expected"]
            assert all(item["countryId"] == country_id for item in report["matched"])
    finally:
        connection.close()


def test_memberships_persist_in_gamestate(tmp_path):
    import shutil
    db = tmp_path / "game.db"
    shutil.copyfile(STATE, db)
    service = ManagerService(str(db))
    for country_id in (3, 72):
        result = service._import_first_division_membership(country_id)
        assert result["unmatched"] == []
        assert result["ambiguous"] == []
        assert len(result["matched"]) == result["expected"]
        count = service.connection.execute("SELECT COUNT(*) FROM first_division_membership WHERE country_id=?", (country_id,)).fetchone()[0]
        assert count == len(result["matched"])


def test_sources_have_official_urls_and_seasons():
    sources = {source.country_id: source for source in FIRST_DIVISION_SOURCES}
    for country_id in (3, 72):
        assert sources[country_id].source_url.startswith("https://")
        assert sources[country_id].season_label in {"2026/27", "2026"}
