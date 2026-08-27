import sqlite3
from engine.world.calendar import CalendarService

def test_calendar_preview_phase_and_deterministic_draw():
    service = CalendarService(sqlite3.connect(':memory:'))
    season = 1
    service.create_period(season, 'REGULAR', '2026-01-01', '2026-01-30', club_id=10)
    preview = service.rest_preview(season, 10, '2026-01-05', '2026-01-06')
    assert preview['persisted'] is False and preview['available'] is False
    phase = service.phase_rule(3, 'Semifinal', 1, 'dois jogos')
    assert phase['phase_order'] == 1
    first = service.deterministic_draw(3, season, [1, 2, 3, 4], 42)
    second = service.deterministic_draw(3, season, [1, 2, 3, 4], 42)
    assert first['clubs'] == second['clubs']
    service.close()
