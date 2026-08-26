import sqlite3
from engine.social.reputation import ReputationService

def test_competition_reputation_preview_snapshot_alert_and_recovery_plan():
    service = ReputationService(sqlite3.connect(':memory:'))
    preview = service.preview_event(1, 9, 2026, 'FAIR_PLAY', 2, -4)
    assert preview['persisted'] is False and preview['projected'] == 46
    service.record_event(1, 9, 2026, 'FAIR_PLAY', 2, -4, 'match-1')
    assert service.snapshot(1, 9, 2026, 1) == 46
    service.record_event(1, 9, 2026, 'PUNISHMENT', 5, -5, 'discipline-1')
    assert service.alerts(1, 2026) == []
    plan = service.create_plan(1, 60, '2026-12-31')
    assert service.approve_plan(plan)['status'] == 'APPROVED'
    service.close()
