from pathlib import Path
import sqlite3
import shutil

import pytest

from engine.competitions.match_engine import CompetitionService, MatchResult
from engine.competitions.structure import CompetitionStructureService

ENGINE = Path(__file__).resolve().parents[1]


def clone_state(tmp_path: Path) -> Path:
    target = tmp_path / 'competition.db'
    source = sqlite3.connect(ENGINE / 'data/state/game.db')
    target_connection = sqlite3.connect(target)
    source.backup(target_connection)
    source.close()
    target_connection.close()
    return target


def test_rules_penalties_champion_prizes_transitions_and_alerts_are_idempotent(tmp_path):
    path = clone_state(tmp_path)
    matches = CompetitionService(path)
    season = matches.create_season(2098)
    competition = matches.create_competition('Copa P0', season, [1, 2])
    fixtures = matches.generate_fixtures(competition)
    match_id = fixtures[0]
    structure = CompetitionStructureService(path)
    structure.configure_rules(competition, penalty_shootout_enabled=True, promotion_slots=1, relegation_slots=1)
    winner = structure.resolve_penalty_shootout(match_id, 4, 3)
    assert winner == 'HOME'
    assert structure.connection.execute("SELECT COUNT(*) FROM match_events WHERE match_id=? AND event_type='PENALTY_SHOOTOUT'", (match_id,)).fetchone()[0] == 1
    matches.play(match_id, seed=9)
    # O fixture estrutural tem fluxo independente; marcamos a fixture como jogada
    structure.connection.execute("UPDATE fixtures SET status='PLAYED' WHERE competition_id=?", (competition,))
    structure.connection.commit()
    assert structure.finish_competition(competition) is True
    assert structure.connection.execute('SELECT COUNT(*) FROM competition_champions WHERE competition_id=?', (competition,)).fetchone()[0] == 1
    structure.set_prizes(competition, {1: 1000, 2: 500})
    assert structure.award_prizes(competition) == 2
    assert structure.award_prizes(competition) == 0
    assert structure.record_transitions(competition, [1], [2]) == 2
    assert structure.record_transitions(competition, [1], [2]) == 0
    assert structure.emit_classification_alerts(competition) >= 1
    assert structure.emit_classification_alerts(competition) == 0
    structure.close()
    matches.close()


def test_transition_and_penalty_limits_are_enforced(tmp_path):
    path = clone_state(tmp_path)
    matches = CompetitionService(path)
    season = matches.create_season(2097)
    competition = matches.create_competition('Regras P0', season, [1, 2])
    match_id = matches.generate_fixtures(competition)[0]
    structure = CompetitionStructureService(path)
    structure.configure_rules(competition, penalty_shootout_enabled=False, promotion_slots=0, relegation_slots=0)
    with pytest.raises(ValueError, match='PENALTY_SHOOTOUT_NOT_ENABLED'):
        structure.resolve_penalty_shootout(match_id, 3, 2)
    with pytest.raises(ValueError, match='TRANSITION_LIMIT_EXCEEDED'):
        structure.record_transitions(competition, [1], [])
    structure.close()
    matches.close()
