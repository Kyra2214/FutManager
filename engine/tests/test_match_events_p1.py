from __future__ import annotations

import sqlite3

import pytest

from engine.competitions.match_engine import CompetitionService


def make_service():
    service = CompetitionService(sqlite3.connect(':memory:'))
    season = service.create_season(2026)
    competition = service.create_competition('Liga', season, [1, 2])
    return service, service.generate_fixtures(competition)[0]


def test_events_are_ordered_and_preview_does_not_persist():
    service, match_id = make_service()
    before = service.connection.total_changes
    preview = service.preview_result(match_id, seed=7)
    assert preview['persisted'] is False and service.connection.total_changes == before
    service.record_event(match_id, 'GOAL', 12, 10, {'team': 1})
    with pytest.raises(ValueError, match='MATCH_EVENT_OUT_OF_ORDER'):
        service.record_event(match_id, 'CARD', 8, 10)
    assert service.match_events(match_id)[0]['event_type'] == 'GOAL'
    service.close()


def test_official_summary_and_reprocess_audit():
    service, match_id = make_service()
    service.play(match_id, seed=3)
    summary = service.official_summary(match_id)
    assert summary['official'] is True
    audit = service.reprocess_result(match_id, 'correção administrativa')
    assert audit['status'] == 'REPROCESS_REQUESTED'
    service.close()
