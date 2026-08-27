from pathlib import Path
import sqlite3

import pytest

from engine.competitions.match_engine import CompetitionService
from engine.manager.career import ManagerService
from scripts.career_gateway import play_controlled_match

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/database/game.db"


def clone(path: Path) -> None:
    source = sqlite3.connect(BASE)
    target = sqlite3.connect(path)
    source.backup(target)
    source.close()
    target.close()


def test_controlled_match_is_played_and_external_match_is_rejected(tmp_path):
    path = tmp_path / "controlled-match.db"
    clone(path)
    manager = ManagerService(path)
    manager.start_career("Ana", "BR", 31, "Carreira controlada", "club", 1)
    competition = CompetitionService(manager.connection)
    season_id = competition.create_season(2099)
    controlled_competition = competition.create_competition("Partida controlada", season_id, [1, 2])
    controlled_match_id = competition.generate_fixtures(controlled_competition, start_date="2099-01-10")[0]
    external_competition = competition.create_competition("Partida externa", season_id, [2, 3])
    external_match_id = competition.generate_fixtures(external_competition, start_date="2099-01-10")[0]

    result = play_controlled_match(manager.connection, {
        "match_id": controlled_match_id,
        "seed": 77,
        "decisions": {
            "tactics": {"mentality": "OFFENSIVE", "attackLane": "WINGS", "passing": "SHORT", "pressure": "HIGH", "crossing": True},
            "substitutions": [{"playerOutId": 2, "playerInId": 3}],
            "penalty_taker_id": 1,
            "red_card_response": {"formation": "4-3-3", "mentality": "DEFENSIVE"},
        },
    })

    assert result["status"] == "PLAYED"
    assert len(result["control_events"]) == 4
    assert manager.connection.execute("SELECT COUNT(*) FROM match_control_decisions WHERE match_id=?", (controlled_match_id,)).fetchone()[0] == 4
    assert result["controlled_club_id"] == 1
    assert manager.connection.execute("SELECT status,home_goals,away_goals FROM matches WHERE match_id=?", (controlled_match_id,)).fetchone()[0] == "PLAYED"
    with pytest.raises(ValueError, match="CONTROLLED_MATCH_REQUIRED"):
        play_controlled_match(manager.connection, {"match_id": external_match_id, "seed": 78})
    assert manager.connection.execute("SELECT status FROM matches WHERE match_id=?", (external_match_id,)).fetchone()[0] == "SCHEDULED"
    with pytest.raises(ValueError, match="MATCH_NOT_SCHEDULED"):
        play_controlled_match(manager.connection, {"match_id": controlled_match_id, "seed": 79})
    manager.close()
