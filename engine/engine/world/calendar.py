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
CREATE TABLE IF NOT EXISTS competition_draws(draw_id INTEGER PRIMARY KEY AUTOINCREMENT,competition_id INTEGER NOT NULL,season_id INTEGER NOT NULL,seed INTEGER NOT NULL,draw_order TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(competition_id,season_id));
CREATE TABLE IF NOT EXISTS calendar_phase_rules(phase_id INTEGER PRIMARY KEY AUTOINCREMENT,competition_id INTEGER NOT NULL,name TEXT NOT NULL,phase_order INTEGER NOT NULL,rule TEXT NOT NULL,UNIQUE(competition_id,phase_order));
CREATE TABLE IF NOT EXISTS national_holidays(holiday_id INTEGER PRIMARY KEY AUTOINCREMENT,country_id INTEGER NOT NULL,holiday_date TEXT NOT NULL,name TEXT NOT NULL,UNIQUE(country_id,holiday_date));
CREATE TABLE IF NOT EXISTS fifa_windows(window_id INTEGER PRIMARY KEY AUTOINCREMENT,start_date TEXT NOT NULL,end_date TEXT NOT NULL,name TEXT NOT NULL,UNIQUE(start_date,end_date));
CREATE TABLE IF NOT EXISTS stadium_timezones(club_id INTEGER PRIMARY KEY,timezone TEXT NOT NULL,utc_offset_minutes INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS schedule_adjustments(adjustment_id INTEGER PRIMARY KEY AUTOINCREMENT,calendar_id INTEGER NOT NULL,reason TEXT NOT NULL,old_start TEXT NOT NULL,new_start TEXT NOT NULL,priority INTEGER NOT NULL,created_at TEXT NOT NULL,UNIQUE(calendar_id,new_start));
CREATE TABLE IF NOT EXISTS competition_priorities(competition_id INTEGER PRIMARY KEY,priority INTEGER NOT NULL CHECK(priority>=0));
CREATE TABLE IF NOT EXISTS registration_windows(window_id INTEGER PRIMARY KEY AUTOINCREMENT,season_id INTEGER NOT NULL,category TEXT NOT NULL,start_date TEXT NOT NULL,end_date TEXT NOT NULL,UNIQUE(season_id,category));
CREATE TABLE IF NOT EXISTS travel_rules(rule_id INTEGER PRIMARY KEY AUTOINCREMENT,origin_country INTEGER NOT NULL,destination_country INTEGER NOT NULL,mode TEXT NOT NULL,duration_days INTEGER NOT NULL,cost INTEGER NOT NULL,UNIQUE(origin_country,destination_country,mode));
CREATE TABLE IF NOT EXISTS calendar_audit(audit_id INTEGER PRIMARY KEY AUTOINCREMENT,calendar_id INTEGER NOT NULL,action TEXT NOT NULL,old_value TEXT,new_value TEXT,created_at TEXT NOT NULL);
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

    def add_national_holiday(self, country_id: int, holiday_date: str, name: str) -> int:
        date.fromisoformat(holiday_date)
        with self.connection:
            cur=self.connection.execute('INSERT OR IGNORE INTO national_holidays(country_id,holiday_date,name) VALUES(?,?,?)',(country_id,holiday_date,name))
            if cur.rowcount: return int(cur.lastrowid)
        return int(self.connection.execute('SELECT holiday_id FROM national_holidays WHERE country_id=? AND holiday_date=?',(country_id,holiday_date)).fetchone()['holiday_id'])

    def add_fifa_window(self, start_date: str, end_date: str, name: str) -> int:
        self._date_range(start_date,end_date)
        with self.connection:
            cur=self.connection.execute('INSERT OR IGNORE INTO fifa_windows(start_date,end_date,name) VALUES(?,?,?)',(start_date,end_date,name))
        row=self.connection.execute('SELECT window_id FROM fifa_windows WHERE start_date=? AND end_date=?',(start_date,end_date)).fetchone(); return int(row['window_id'])

    def set_stadium_timezone(self, club_id: int, timezone: str, utc_offset_minutes: int) -> dict:
        with self.connection: self.connection.execute('INSERT OR REPLACE INTO stadium_timezones(club_id,timezone,utc_offset_minutes) VALUES(?,?,?)',(club_id,timezone,utc_offset_minutes))
        return dict(self.connection.execute('SELECT * FROM stadium_timezones WHERE club_id=?',(club_id,)).fetchone())

    def set_competition_priority(self, competition_id: int, priority: int) -> dict:
        if int(priority)<0: raise ValueError('PRIORITY_INVALID')
        with self.connection: self.connection.execute('INSERT OR REPLACE INTO competition_priorities(competition_id,priority) VALUES(?,?)',(competition_id,priority))
        return dict(self.connection.execute('SELECT * FROM competition_priorities WHERE competition_id=?',(competition_id,)).fetchone())

    def adjust_fixture(self, calendar_id: int, new_start: str, reason: str, priority: int = 50) -> dict:
        date.fromisoformat(new_start)
        row=self.connection.execute('SELECT * FROM season_calendar WHERE calendar_id=?',(calendar_id,)).fetchone()
        if not row: raise KeyError(calendar_id)
        with self.connection:
            self.connection.execute('INSERT OR IGNORE INTO schedule_adjustments(calendar_id,reason,old_start,new_start,priority,created_at) VALUES(?,?,?,?,?,?)',(calendar_id,reason,row['start_date'],new_start,priority,date.today().isoformat()))
            self.connection.execute('UPDATE season_calendar SET start_date=?,end_date=? WHERE calendar_id=?',(new_start,new_start,calendar_id))
            self.connection.execute('INSERT INTO calendar_audit(calendar_id,action,old_value,new_value,created_at) VALUES(?,?,?,?,?)',(calendar_id,'RESCHEDULE',row['start_date'],new_start,date.today().isoformat()))
        return dict(self.connection.execute('SELECT * FROM schedule_adjustments WHERE calendar_id=? AND new_start=?',(calendar_id,new_start)).fetchone())

    def international_window_conflicts(self, season_id: int, club_id: int) -> list[dict]:
        return [dict(r) for r in self.connection.execute('SELECT c.*,w.name AS fifa_window FROM season_calendar c JOIN fifa_windows w ON c.start_date<=w.end_date AND c.end_date>=w.start_date WHERE c.season_id=? AND c.club_id=?',(season_id,club_id)).fetchall()]

    def add_registration_window(self, season_id: int, category: str, start_date: str, end_date: str) -> dict:
        self._date_range(start_date,end_date)
        with self.connection: self.connection.execute('INSERT OR REPLACE INTO registration_windows(season_id,category,start_date,end_date) VALUES(?,?,?,?)',(season_id,category,start_date,end_date))
        return dict(self.connection.execute('SELECT * FROM registration_windows WHERE season_id=? AND category=?',(season_id,category)).fetchone())

    def set_travel_rule(self, origin_country: int, destination_country: int, mode: str, duration_days: int, cost: int) -> dict:
        if int(duration_days)<0 or int(cost)<0: raise ValueError('TRAVEL_RULE_INVALID')
        with self.connection: self.connection.execute('INSERT OR REPLACE INTO travel_rules(origin_country,destination_country,mode,duration_days,cost) VALUES(?,?,?,?,?)',(origin_country,destination_country,mode,duration_days,cost))
        return dict(self.connection.execute('SELECT * FROM travel_rules WHERE origin_country=? AND destination_country=? AND mode=?',(origin_country,destination_country,mode)).fetchone())

    def travel_preview(self, origin_country: int, destination_country: int, mode: str) -> dict:
        row=self.connection.execute('SELECT * FROM travel_rules WHERE origin_country=? AND destination_country=? AND mode=?',(origin_country,destination_country,mode)).fetchone()
        return {'available':row is not None,'duration_days':int(row['duration_days']) if row else None,'cost':int(row['cost']) if row else None,'persisted':False}

    def minimum_rest(self, season_id: int, club_id: int, candidate_date: str, minimum_days: int = 2) -> dict:
        candidate=date.fromisoformat(candidate_date); previous=self.connection.execute('SELECT MAX(end_date) AS last_date FROM season_calendar WHERE season_id=? AND club_id=? AND end_date<?',(season_id,club_id,candidate_date)).fetchone()['last_date']
        gap=(candidate-date.fromisoformat(previous)).days if previous else None
        return {'available':gap is None or gap>=int(minimum_days),'gap_days':gap,'minimum_days':int(minimum_days)}

    def overlap_preview(self, season_id: int, club_id: int, start_date: str, end_date: str) -> dict:
        self._date_range(start_date,end_date)
        rows=self.connection.execute('SELECT calendar_id FROM season_calendar WHERE season_id=? AND club_id=? AND start_date<=? AND end_date>=?',(season_id,club_id,end_date,start_date)).fetchall()
        return {'blocked':bool(rows),'calendar_ids':[int(r['calendar_id']) for r in rows],'persisted':False}

    def season_preview(self, season_id: int) -> dict:
        rows=self.connection.execute('SELECT calendar_type,COUNT(*) AS count,MIN(start_date) AS start_date,MAX(end_date) AS end_date FROM season_calendar WHERE season_id=? GROUP BY calendar_type ORDER BY calendar_type',(season_id,)).fetchall()
        return {'season_id':int(season_id),'categories':[dict(r) for r in rows],'overlaps':sum(len(self.detect_conflicts(season_id,int(r['club_id']))) for r in self.connection.execute('SELECT DISTINCT club_id FROM season_calendar WHERE season_id=? AND club_id IS NOT NULL',(season_id,)).fetchall()),'persisted':False}

    def audit_changes(self, calendar_id: int) -> list[dict]:
        return [dict(r) for r in self.connection.execute('SELECT * FROM calendar_audit WHERE calendar_id=? ORDER BY audit_id',(calendar_id,)).fetchall()]

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

    def rest_preview(self, season_id: int, club_id: int, start_date: str, end_date: str) -> dict[str, object]:
        self._date_range(start_date, end_date)
        overlap = self.connection.execute('SELECT COUNT(*) AS total FROM season_calendar WHERE season_id=? AND club_id=? AND start_date<=? AND end_date>=?', (int(season_id), int(club_id), end_date, start_date)).fetchone()
        return {'season_id': int(season_id), 'club_id': int(club_id), 'start_date': start_date, 'end_date': end_date, 'conflicting_commitments': int(overlap['total']), 'available': int(overlap['total']) == 0, 'persisted': False}

    def phase_rule(self, competition_id: int, name: str, phase_order: int, rule: str) -> dict:
        if not str(name).strip() or int(phase_order) < 1 or not str(rule).strip(): raise ValueError('PHASE_RULE_INVALID')
        self.connection.execute('INSERT INTO calendar_phase_rules(competition_id,name,phase_order,rule) VALUES(?,?,?,?) ON CONFLICT(competition_id,phase_order) DO UPDATE SET name=excluded.name,rule=excluded.rule', (int(competition_id), str(name).strip(), int(phase_order), str(rule).strip())); self.connection.commit()
        return dict(self.connection.execute('SELECT * FROM calendar_phase_rules WHERE competition_id=? AND phase_order=?', (int(competition_id), int(phase_order))).fetchone())

    def deterministic_draw(self, competition_id: int, season_id: int, clubs: list[int], seed: int) -> dict:
        import random
        if len(clubs) < 2 or len(set(clubs)) != len(clubs): raise ValueError('DRAW_CLUBS_INVALID')
        order = list(map(int, clubs)); random.Random(int(seed)).shuffle(order)
        encoded = ','.join(map(str, order))
        with self.connection:
            self.connection.execute('INSERT INTO competition_draws(competition_id,season_id,seed,draw_order,created_at) VALUES(?,?,?,?,?) ON CONFLICT(competition_id,season_id) DO UPDATE SET seed=excluded.seed,draw_order=excluded.draw_order,created_at=excluded.created_at', (int(competition_id), int(season_id), int(seed), encoded, date.today().isoformat()))
        row = self.connection.execute('SELECT * FROM competition_draws WHERE competition_id=? AND season_id=?', (int(competition_id), int(season_id))).fetchone()
        return {**dict(row), 'clubs': tuple(order)}

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
