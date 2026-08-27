from __future__ import annotations

import sqlite3

from engine.competitions.match_engine import CompetitionService


def make_service():
    service = CompetitionService(sqlite3.connect(':memory:'))
    season = service.create_season(2026)
    competition = service.create_competition('Liga', season, [1, 2])
    match_id = service.generate_fixtures(competition)[0]
    return service, match_id


def test_fixture_preview_configuration_and_cancel():
    service, match_id = make_service()
    before = service.connection.total_changes
    preview = service.preview_fixture(match_id)
    assert preview['persisted'] is False and preview['operationally_ready'] is False
    assert service.connection.total_changes == before
    configured = service.configure_fixture(match_id, 7, 'NEUTRAL', 99, 'RAIN', 'HIGH')
    assert configured['venue_type'] == 'NEUTRAL'
    assert service.preview_fixture(match_id)['operationally_ready'] is True
    cancelled = service.cancel_fixture(match_id, 'clima extremo')
    assert cancelled['status'] == 'CANCELLED'
    service.close()


def test_played_fixture_can_be_closed_formally():
    service, match_id = make_service()
    result = service.play(match_id, seed=10)
    assert result.match_id == match_id
    closed = service.close_fixture(match_id)
    assert closed['closed_at']
    service.close()
