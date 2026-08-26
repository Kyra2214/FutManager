import sqlite3
from engine.scouting.service import ScoutService

def test_opponent_observation_report_plan_quality_and_expiry():
    service = ScoutService(sqlite3.connect(':memory:'))
    row = service.observe_opponent(1, 2, 9, 2026, 'HIGH_PRESS', 'costas da defesa', 'fixture:44:eventos', 0.8, 5, '2026-06-01')
    assert row['status'] == 'ACTIVE'
    report = service.opponent_report(1, 2, 9, 2026)
    assert report['quality'] == 0.8 and report['reports'][0]['evidence'] == 'fixture:44:eventos'
    assert service.preview_game_plan(1, 2, row['observation_id'], 'bloquear transição')['persisted'] is False
    assert service.approve_game_plan(1, 2, row['observation_id'], 'bloquear transição')['status'] == 'APPROVED'
    assert service.compare_opponents(1, [2], 9, 2026)[0]['weaknesses'] == ['costas da defesa']
    assert service.expire_opponent_reports('2027-01-01') == 1
    service.close()
