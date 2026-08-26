from pathlib import Path
import sqlite3

from engine.world.calendar import CalendarService
from engine.world.time_and_finance import LogicalClock

ENGINE = Path(__file__).resolve().parents[1]


def temp_db(tmp_path: Path) -> Path:
    path = tmp_path / 'calendar.db'
    source = sqlite3.connect(ENGINE / 'data/state/game.db')
    target = sqlite3.connect(path)
    source.backup(target)
    source.close()
    target.close()
    return path


def test_calendar_preseason_rest_conflict_empty_week_and_congestion(tmp_path):
    path = temp_db(tmp_path)
    calendar = CalendarService(path)
    preseason = calendar.create_preseason(2098, '2098-01-01', '2098-01-14')
    regular = calendar.create_regular_season(2098, '2098-01-15', '2098-11-30', competition_id=1)
    calendar.add_rest_window(2098, 1, '2098-02-01', '2098-02-03')
    one = calendar.create_period(2098, 'FINAL', '2098-03-01', '2098-03-01', competition_id=1, club_id=1)
    two = calendar.create_period(2098, 'FINAL', '2098-03-01', '2098-03-01', competition_id=2, club_id=1)
    conflicts = calendar.detect_conflicts(2098, 1)
    assert conflicts
    conflict_id = calendar.connection.execute('SELECT conflict_id FROM calendar_conflicts ORDER BY conflict_id DESC LIMIT 1').fetchone()[0]
    calendar.reschedule_conflict(conflict_id, '2098-03-02')
    assert calendar.connection.execute('SELECT resolution FROM calendar_conflicts WHERE conflict_id=?', (conflict_id,)).fetchone()[0] == 'RESCHEDULED'
    assert calendar.week_summary(2098, '2098-12-01')['scheduled_items'] == 0
    assert calendar.congestion_report(2098, threshold=2)
    assert preseason != regular and one != two
    calendar.close()


def test_logical_clock_day_week_history_and_restore(tmp_path):
    path = temp_db(tmp_path)
    connection = sqlite3.connect(path)
    clock = LogicalClock(connection)
    day = clock.next_day_context(seed=5)
    week = clock.next_week_context(seed=7)
    clock.commit_tick(day)
    assert clock.current()['current_date'] == day.current_date.isoformat()
    clock.restore('2026-01-01', 1, 1, 2026, 'rollback-test')
    assert clock.current()['current_date'] == '2026-01-01'
    calendar = CalendarService(connection)
    assert calendar.record_clock_history('rollback-test', 2026, 1, '2026-01-01', 'ROLLBACK') is True
    assert calendar.record_clock_history('rollback-test', 2026, 1, '2026-01-01', 'ROLLBACK') is False
    calendar.close()
