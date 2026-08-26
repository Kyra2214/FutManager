from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path
from typing import Iterator

from engine.core.state_store import assert_mutable_state_path

SCHEMA = '''
CREATE TABLE IF NOT EXISTS season_calendar(
    calendar_id INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id INTEGER NOT NULL,
    calendar_type TEXT NOT NULL CHECK(calendar_type IN ('PRESEASON','REGULAR','BREAK','FINAL')),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    competition_id INTEGER,
    club_id INTEGER,
    status TEXT NOT NULL DEFAULT 'PLANNED',
    source TEXT NOT NULL,
    UNIQUE(season_id,calendar_type,start_date,end_date,competition_id,club_id)
);
CREATE TABLE IF NOT EXISTS rest_windows(
    rest_window_id INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id INTEGER NOT NULL,
    club_id INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    source TEXT NOT NULL,
    UNIQUE(season_id,club_id,start_date,end_date)
);
CREATE TABLE IF NOT EXISTS calendar_conflicts(
    conflict_id INTEGER PRIMARY KEY AUTOINCREMENT,
    season_id INTEGER NOT NULL,
    club_id INTEGER NOT NULL,
    first_calendar_id INTEGER NOT NULL,
    second_calendar_id INTEGER NOT NULL,
    resolution TEXT NOT NULL CHECK(resolution IN ('PENDING','RESCHEDULED','ACCEPTED')),
    resolved_date TEXT,
    source TEXT NOT NULL,
    UNIQUE(first_calendar_id,second_calendar_id)
);
CREATE TABLE IF NOT EXISTS clock_history(
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tick_id TEXT NOT NULL,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    current_date TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('ADVANCE_WEEK','ADVANCE_DAY','ROLLBACK')),
    source TEXT NOT NULL,
    UNIQUE(tick_id,action)
);
CREATE INDEX IF NOT EXISTS idx_season_calendar_club_dates ON season_calendar(season_id,club_id,start_date,end_date);
CREATE INDEX IF NOT EXISTS idx_rest_windows_dates ON rest_windows(season_id,club_id,start_date,end_date);
'''


class CalendarService:
    def __init__(self, db: str | Path | sqlite3.Connection):
        if isinstance(db, sqlite3.Connection):
            self.connection = db
        else:
            assert_mutable_state_path(db)
            self.connection = sqlite3.connect(str(db))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    @contextmanager
    def transaction(self, managed_transaction: bool = True) -> Iterator[None]:
        if not managed_transaction:
            yield
            return
        with self.connection:
            yield

    def _date_range(self, start_date: str, end_date: str) -> tuple[date, date]:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        if end < start:
            raise ValueError('CALENDAR_RANGE_INVALID')
        return start, end

    def create_period(self, season_id: int, calendar_type: str, start_date: str, end_date: str, competition_id: int | None = None, club_id: int | None = None, source: str = 'observed', managed_transaction: bool = True) -> int:
        if calendar_type not in {'PRESEASON', 'REGULAR', 'BREAK', 'FINAL'}:
            raise ValueError('CALENDAR_TYPE_INVALID')
        self._date_range(start_date, end_date)
        with self.transaction(managed_transaction):
            cur = self.connection.execute('''INSERT OR IGNORE INTO season_calendar(season_id,calendar_type,start_date,end_date,competition_id,club_id,source)
                VALUES(?,?,?,?,?,?,?)''', (season_id, calendar_type, start_date, end_date, competition_id, club_id, source))
            if cur.rowcount == 0:
                row = self.connection.execute('''SELECT calendar_id FROM season_calendar WHERE season_id=? AND calendar_type=? AND start_date=? AND end_date=? AND competition_id IS ? AND club_id IS ?''', (season_id, calendar_type, start_date, end_date, competition_id, club_id)).fetchone()
                return int(row['calendar_id'])
            return int(cur.lastrowid)

    def create_preseason(self, season_id: int, start_date: str, end_date: str, source: str = 'observed') -> int:
        return self.create_period(season_id, 'PRESEASON', start_date, end_date, source=source)

    def create_regular_season(self, season_id: int, start_date: str, end_date: str, competition_id: int | None = None, source: str = 'observed') -> int:
        return self.create_period(season_id, 'REGULAR', start_date, end_date, competition_id=competition_id, source=source)

    def add_rest_window(self, season_id: int, club_id: int, start_date: str, end_date: str, source: str = 'observed') -> int:
        self._date_range(start_date, end_date)
        with self.transaction():
            cur = self.connection.execute('INSERT OR IGNORE INTO rest_windows(season_id,club_id,start_date,end_date,source) VALUES(?,?,?,?,?)', (season_id, club_id, start_date, end_date, source))
            if cur.rowcount == 0:
                row = self.connection.execute('SELECT rest_window_id FROM rest_windows WHERE season_id=? AND club_id=? AND start_date=? AND end_date=?', (season_id, club_id, start_date, end_date)).fetchone()
                return int(row['rest_window_id'])
            return int(cur.lastrowid)

    def club_agenda(self, season_id: int, club_id: int) -> list[dict[str, object]]:
        return [dict(row) for row in self.connection.execute('SELECT * FROM season_calendar WHERE season_id=? AND club_id=? ORDER BY start_date,calendar_id', (season_id, club_id)).fetchall()]

    def detect_conflicts(self, season_id: int, club_id: int) -> list[dict[str, object]]:
        rows = self.connection.execute('''SELECT a.calendar_id first_calendar_id,b.calendar_id second_calendar_id,a.start_date first_date,a.end_date first_end,b.start_date second_date,b.end_date second_end
            FROM season_calendar a JOIN season_calendar b ON a.calendar_id < b.calendar_id AND a.season_id=b.season_id AND a.club_id=b.club_id
            WHERE a.season_id=? AND a.club_id=? AND a.start_date <= b.end_date AND b.start_date <= a.end_date''', (season_id, club_id)).fetchall()
        conflicts: list[dict[str, object]] = []
        for row in rows:
            self.connection.execute('INSERT OR IGNORE INTO calendar_conflicts(season_id,club_id,first_calendar_id,second_calendar_id,resolution,source) VALUES(?,?,?,?,?,?)', (season_id, club_id, row['first_calendar_id'], row['second_calendar_id'], 'PENDING', 'calendar.detect_conflicts'))
            conflicts.append(dict(row))
        self.connection.commit()
        return conflicts

    def reschedule_conflict(self, conflict_id: int, resolved_date: str) -> None:
        date.fromisoformat(resolved_date)
        row = self.connection.execute('SELECT conflict_id FROM calendar_conflicts WHERE conflict_id=?', (conflict_id,)).fetchone()
        if row is None:
            raise KeyError(f'CALENDAR_CONFLICT_NOT_FOUND:{conflict_id}')
        self.connection.execute('UPDATE calendar_conflicts SET resolution=?,resolved_date=? WHERE conflict_id=?', ('RESCHEDULED', resolved_date, conflict_id))
        self.connection.commit()

    def week_summary(self, season_id: int, week_start: str) -> dict[str, int | str]:
        start = date.fromisoformat(week_start)
        end = start + timedelta(days=6)
        rows = self.connection.execute('SELECT COUNT(*) AS total,COUNT(DISTINCT club_id) AS clubs FROM season_calendar WHERE season_id=? AND start_date<=? AND end_date>=?', (season_id, end.isoformat(), start.isoformat())).fetchone()
        return {'season_id': season_id, 'week_start': start.isoformat(), 'scheduled_items': int(rows['total']), 'clubs': int(rows['clubs'])}

    def congestion_report(self, season_id: int, threshold: int = 2) -> list[dict[str, object]]:
        if threshold < 1:
            raise ValueError('CONGESTION_THRESHOLD_INVALID')
        rows = self.connection.execute('''SELECT club_id,start_date,COUNT(*) AS commitments FROM season_calendar WHERE season_id=? AND club_id IS NOT NULL GROUP BY club_id,start_date HAVING COUNT(*)>=? ORDER BY start_date,club_id''', (season_id, threshold)).fetchall()
        return [dict(row) for row in rows]

    def record_clock_history(self, tick_id: str, season: int, week: int, current_date: str, action: str, source: str = 'logical_clock') -> bool:
        date.fromisoformat(current_date)
        cur = self.connection.execute('INSERT OR IGNORE INTO clock_history(tick_id,season,week,current_date,action,source) VALUES(?,?,?,?,?,?)', (tick_id, season, week, current_date, action, source))
        self.connection.commit()
        return cur.rowcount == 1

    def close(self) -> None:
        self.connection.close()
