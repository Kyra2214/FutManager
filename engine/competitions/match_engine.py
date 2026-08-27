from __future__ import annotations

import json
import random
import sqlite3
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterator

from engine.core.state_store import assert_mutable_state_path

SCHEMA = '''
CREATE TABLE IF NOT EXISTS seasons(
    season_id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER UNIQUE NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PLANNED'
);
CREATE TABLE IF NOT EXISTS competitions(
    competition_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country_id INTEGER,
    season_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    club_count INTEGER NOT NULL,
    format TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE'
);
CREATE TABLE IF NOT EXISTS competition_entries(
    competition_id INTEGER NOT NULL,
    club_id INTEGER NOT NULL,
    season_id INTEGER NOT NULL,
    PRIMARY KEY(competition_id, club_id)
);
CREATE TABLE IF NOT EXISTS matches(
    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_id INTEGER,
    season_id INTEGER NOT NULL,
    match_date TEXT NOT NULL,
    round INTEGER NOT NULL,
    home_club_id INTEGER NOT NULL,
    away_club_id INTEGER NOT NULL,
    home_lineup_id INTEGER,
    away_lineup_id INTEGER,
    home_goals INTEGER,
    away_goals INTEGER,
    status TEXT NOT NULL DEFAULT 'SCHEDULED',
    seed INTEGER,
    home_form INTEGER NOT NULL DEFAULT 0,
    away_form INTEGER NOT NULL DEFAULT 0,
    home_morale INTEGER NOT NULL DEFAULT 0,
    away_morale INTEGER NOT NULL DEFAULT 0,
    home_tactic INTEGER NOT NULL DEFAULT 0,
    away_tactic INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS match_events(
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    minute INTEGER,
    player_id INTEGER,
    payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS match_stats(
    match_id INTEGER PRIMARY KEY,
    home_shots INTEGER NOT NULL DEFAULT 0,
    away_shots INTEGER NOT NULL DEFAULT 0,
    home_possession INTEGER,
    away_possession INTEGER,
    home_expected_goals REAL,
    away_expected_goals REAL,
    home_yellow_cards INTEGER NOT NULL DEFAULT 0,
    away_yellow_cards INTEGER NOT NULL DEFAULT 0,
    home_red_cards INTEGER NOT NULL DEFAULT 0,
    away_red_cards INTEGER NOT NULL DEFAULT 0,
    home_substitutions INTEGER NOT NULL DEFAULT 0,
    away_substitutions INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS match_advanced_stats(match_id INTEGER PRIMARY KEY,home_duels INTEGER NOT NULL DEFAULT 0,away_duels INTEGER NOT NULL DEFAULT 0,home_set_pieces INTEGER NOT NULL DEFAULT 0,away_set_pieces INTEGER NOT NULL DEFAULT 0,home_corners INTEGER NOT NULL DEFAULT 0,away_corners INTEGER NOT NULL DEFAULT 0,home_tactical_fouls INTEGER NOT NULL DEFAULT 0,away_tactical_fouls INTEGER NOT NULL DEFAULT 0,home_conditional_subs INTEGER NOT NULL DEFAULT 0,away_conditional_subs INTEGER NOT NULL DEFAULT 0,interval_plan TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS match_conditions(match_id INTEGER PRIMARY KEY,crowd_effect INTEGER NOT NULL DEFAULT 0,weather_effect INTEGER NOT NULL DEFAULT 0,referee_profile TEXT NOT NULL DEFAULT 'STANDARD',var_enabled INTEGER NOT NULL DEFAULT 0,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS disciplinary_accumulation(player_id INTEGER PRIMARY KEY,yellow_cards INTEGER NOT NULL DEFAULT 0,red_cards INTEGER NOT NULL DEFAULT 0,suspension_matches INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS match_event_reviews(review_id INTEGER PRIMARY KEY AUTOINCREMENT,match_id INTEGER NOT NULL,event_id INTEGER NOT NULL,action TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(match_id,event_id));
CREATE TABLE IF NOT EXISTS post_match_reports(report_id INTEGER PRIMARY KEY AUTOINCREMENT,match_id INTEGER NOT NULL UNIQUE,recovery_days INTEGER NOT NULL,staff_notes TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS match_reprocess_audit(request_id INTEGER PRIMARY KEY AUTOINCREMENT,match_id INTEGER NOT NULL,reason TEXT NOT NULL,seed INTEGER,created_at TEXT NOT NULL,UNIQUE(match_id,reason));
CREATE TABLE IF NOT EXISTS team_competition_stats(
    competition_id INTEGER NOT NULL,
    club_id INTEGER NOT NULL,
    played INTEGER DEFAULT 0,
    wins INTEGER DEFAULT 0,
    draws INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    goals_for INTEGER DEFAULT 0,
    goals_against INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    PRIMARY KEY(competition_id, club_id)
);
CREATE TABLE IF NOT EXISTS player_match_stats(
    match_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    minutes INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    cards INTEGER DEFAULT 0,
    rating REAL,
    PRIMARY KEY(match_id, player_id)
);
'''

MAX_MATCH_EVENTS = 64


@dataclass(frozen=True)
class MatchResult:
    match_id: int
    home_goals: int
    away_goals: int
    seed: int | None = None
    home_shots: int = 0
    away_shots: int = 0
    home_possession: int | None = None
    away_possession: int | None = None
    home_expected_goals: float | None = None
    away_expected_goals: float | None = None


class CompetitionService:
    def __init__(self, db: str | Path | sqlite3.Connection):
        if not isinstance(db, sqlite3.Connection):
            assert_mutable_state_path(db)
            self.connection = sqlite3.connect(str(db))
        else:
            self.connection = db
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.executescript(SCHEMA)
        self._ensure_match_columns()
        self.connection.commit()

    def _ensure_match_columns(self) -> None:
        existing = {row[1] for row in self.connection.execute('PRAGMA table_info(matches)')}
        definitions = {
            'competition_id': 'INTEGER',
            'home_form': 'INTEGER NOT NULL DEFAULT 0',
            'away_form': 'INTEGER NOT NULL DEFAULT 0',
            'home_morale': 'INTEGER NOT NULL DEFAULT 0',
            'away_morale': 'INTEGER NOT NULL DEFAULT 0',
            'home_tactic': 'INTEGER NOT NULL DEFAULT 0',
            'away_tactic': 'INTEGER NOT NULL DEFAULT 0',
            'referee_id': 'INTEGER',
            'venue_id': 'INTEGER',
            'venue_type': "TEXT NOT NULL DEFAULT 'HOME'",
            'weather': "TEXT NOT NULL DEFAULT 'UNKNOWN'",
            'security_level': "TEXT NOT NULL DEFAULT 'STANDARD'",
            'cancel_reason': 'TEXT',
            'closed_at': 'TEXT',
        }
        for name, definition in definitions.items():
            if name not in existing:
                self.connection.execute(f'ALTER TABLE matches ADD COLUMN {name} {definition}')

    @contextmanager
    def transaction(self, managed_transaction: bool = True) -> Iterator[None]:
        if not managed_transaction:
            yield
            return
        with self.connection:
            yield

    def create_season(self, year: int, start_date: str | None = None, end_date: str | None = None) -> int:
        cur = self.connection.execute('INSERT INTO seasons(year,start_date,end_date,status) VALUES(?,?,?,?)', (year, start_date or f'{year}-01-01', end_date or f'{year}-12-31', 'ACTIVE'))
        self.connection.commit()
        return int(cur.lastrowid)

    def create_competition(self, name: str, season_id: int, club_ids: list[int], country_id: int | None = None, type_: str = 'LEAGUE', format_: str = 'ROUND_ROBIN') -> int:
        cur = self.connection.execute('INSERT INTO competitions(name,country_id,season_id,type,club_count,format) VALUES(?,?,?,?,?,?)', (name, country_id, season_id, type_, len(club_ids), format_))
        cid = int(cur.lastrowid)
        for club in club_ids:
            self.connection.execute('INSERT INTO competition_entries VALUES(?,?,?)', (cid, club, season_id))
            self.connection.execute('INSERT OR IGNORE INTO team_competition_stats(competition_id,club_id) VALUES(?,?)', (cid, club))
        self.connection.commit()
        return cid

    def generate_fixtures(self, competition_id: int, start_date: str = '2026-01-10') -> list[int]:
        rows = self.connection.execute('SELECT club_id FROM competition_entries WHERE competition_id=?', (competition_id,)).fetchall()
        clubs = [int(row[0]) for row in rows]
        competition = self.connection.execute('SELECT season_id FROM competitions WHERE competition_id=?', (competition_id,)).fetchone()
        if competition is None:
            raise KeyError(f'COMPETITION_NOT_FOUND:{competition_id}')
        created: list[int] = []
        day = date.fromisoformat(start_date)
        round_number = 1
        for i in range(len(clubs)):
            for j in range(i + 1, len(clubs)):
                cur = self.connection.execute('INSERT INTO matches(competition_id,season_id,match_date,round,home_club_id,away_club_id,seed) VALUES(?,?,?,?,?,?,?)', (competition_id, competition[0], day.isoformat(), round_number, clubs[i], clubs[j], i * 100 + j))
                created.append(int(cur.lastrowid))
                day += timedelta(days=7)
                round_number += 1
        self.connection.commit()
        return created

    def _require_match(self, match_id: int) -> sqlite3.Row:
        match = self.connection.execute('SELECT * FROM matches WHERE match_id=?', (match_id,)).fetchone()
        if match is None:
            raise KeyError(f'MATCH_NOT_FOUND:{match_id}')
        if match['competition_id'] is None:
            raise ValueError('MATCH_WITHOUT_COMPETITION')
        if match['status'] == 'PLAYED':
            raise ValueError('ALREADY_PLAYED')
        return match

    @staticmethod
    def _bounded(value: int, low: int = -20, high: int = 20) -> int:
        return max(low, min(high, int(value)))

    def configure_fixture(self, match_id: int, referee_id: int, venue_type: str = 'HOME', venue_id: int | None = None, weather: str = 'UNKNOWN', security_level: str = 'STANDARD') -> dict:
        match = self._require_match(match_id)
        if venue_type not in {'HOME', 'NEUTRAL'}: raise ValueError('VENUE_TYPE_INVALID')
        if security_level not in {'LOW', 'STANDARD', 'HIGH'}: raise ValueError('SECURITY_LEVEL_INVALID')
        with self.connection:
            self.connection.execute('UPDATE matches SET referee_id=?,venue_id=?,venue_type=?,weather=?,security_level=? WHERE match_id=?', (int(referee_id), venue_id, venue_type, str(weather).strip() or 'UNKNOWN', security_level, int(match_id)))
        return dict(self.connection.execute('SELECT * FROM matches WHERE match_id=?', (int(match_id),)).fetchone())

    def preview_fixture(self, match_id: int) -> dict:
        match = self._require_match(match_id)
        return {'match_id': int(match_id), 'home_club_id': int(match['home_club_id']), 'away_club_id': int(match['away_club_id']), 'match_date': match['match_date'], 'referee_id': match['referee_id'], 'venue_type': match['venue_type'], 'weather': match['weather'], 'security_level': match['security_level'], 'persisted': False, 'operationally_ready': bool(match['referee_id'] and match['venue_id'] or match['venue_type'] == 'NEUTRAL')}

    def cancel_fixture(self, match_id: int, reason: str) -> dict:
        match = self._require_match(match_id)
        if not str(reason).strip(): raise ValueError('CANCEL_REASON_REQUIRED')
        with self.connection:
            self.connection.execute("UPDATE matches SET status='CANCELLED',cancel_reason=? WHERE match_id=?", (str(reason).strip(), int(match_id)))
        return dict(self.connection.execute('SELECT * FROM matches WHERE match_id=?', (int(match_id),)).fetchone())

    def close_fixture(self, match_id: int) -> dict:
        match = self.connection.execute('SELECT * FROM matches WHERE match_id=?', (int(match_id),)).fetchone()
        if match is None: raise KeyError(f'MATCH_NOT_FOUND:{match_id}')
        if match['status'] != 'PLAYED': raise ValueError('FIXTURE_NOT_PLAYED')
        with self.connection:
            self.connection.execute('UPDATE matches SET closed_at=? WHERE match_id=?', (date.today().isoformat(), int(match_id)))
        return dict(self.connection.execute('SELECT * FROM matches WHERE match_id=?', (int(match_id),)).fetchone())

    def generate_result(
        self,
        match_id: int,
        home_strength: int = 70,
        away_strength: int = 65,
        seed: int | None = None,
        home_form: int = 0,
        away_form: int = 0,
        home_morale: int = 0,
        away_morale: int = 0,
        home_tactic: int = 0,
        away_tactic: int = 0,
        persist: bool = True,
    ) -> MatchResult:
        match = self._require_match(match_id)
        chosen_seed = seed if seed is not None else match['seed']
        rng = random.Random(chosen_seed)
        home_context = self._bounded(home_strength - away_strength + home_form - away_form + home_morale - away_morale + home_tactic - away_tactic)
        away_context = -home_context
        home_lambda = max(0.15, 1.15 + home_context / 100 + 0.18)  # mando de campo documentado
        away_lambda = max(0.15, 1.05 + away_context / 100)
        home_goals = max(0, min(12, int(rng.random() * 3 + (0.45 if home_lambda > 1.15 else 0))))
        away_goals = max(0, min(12, int(rng.random() * 3 + (0.35 if away_lambda > 1.15 else 0))))
        if home_context > 0 and rng.random() < min(0.85, 0.55 + home_context / 200):
            home_goals = max(home_goals, away_goals + 1)
        elif away_context > 0 and rng.random() < min(0.85, 0.55 + away_context / 200):
            away_goals = max(away_goals, home_goals + 1)
        home_shots = max(home_goals, 5 + int(rng.random() * 12) + max(0, home_context // 25))
        away_shots = max(away_goals, 4 + int(rng.random() * 12) + max(0, away_context // 25))
        possession_home = max(35, min(65, 50 + home_context // 5 + int(rng.random() * 5 - 2)))
        possession_away = 100 - possession_home
        xg_home = round(min(8.0, home_shots * 0.09 + home_goals * 0.18), 2)
        xg_away = round(min(8.0, away_shots * 0.09 + away_goals * 0.18), 2)
        if persist:
            self.connection.execute('''UPDATE matches SET seed=?,home_form=?,away_form=?,home_morale=?,away_morale=?,home_tactic=?,away_tactic=? WHERE match_id=?''', (chosen_seed, home_form, away_form, home_morale, away_morale, home_tactic, away_tactic, match_id))
        return MatchResult(match_id, home_goals, away_goals, chosen_seed, home_shots, away_shots, possession_home, possession_away, xg_home, xg_away)

    def apply_result(self, result: MatchResult, home_lineup_id: int | None = None, away_lineup_id: int | None = None, managed_transaction: bool = True, max_events: int = MAX_MATCH_EVENTS) -> MatchResult:
        if result.home_goals < 0 or result.away_goals < 0:
            raise ValueError('NEGATIVE_SCORE')
        if max_events < 1 or max_events > MAX_MATCH_EVENTS:
            raise ValueError('EVENT_LIMIT_INVALID')
        match = self._require_match(result.match_id)
        transaction = self.transaction(managed_transaction) if managed_transaction else nullcontext()
        try:
            with transaction:
                self.connection.execute('''UPDATE matches SET home_goals=?,away_goals=?,status='PLAYED',home_lineup_id=?,away_lineup_id=?,seed=? WHERE match_id=?''', (result.home_goals, result.away_goals, home_lineup_id, away_lineup_id, result.seed, result.match_id))
                self.connection.execute('INSERT INTO match_events(match_id,event_type,minute,player_id,payload) VALUES(?,?,?,?,?)', (result.match_id, 'RESULT', 90, None, json.dumps({'home': result.home_goals, 'away': result.away_goals, 'seed': result.seed}, sort_keys=True)))
                self.connection.execute('''INSERT OR REPLACE INTO match_stats(match_id,home_shots,away_shots,home_possession,away_possession,home_expected_goals,away_expected_goals)
                    VALUES(?,?,?,?,?,?,?)''', (result.match_id, result.home_shots, result.away_shots, result.home_possession, result.away_possession, result.home_expected_goals, result.away_expected_goals))
                self._record_lineup_player_stats(result.match_id, home_lineup_id, result.home_goals)
                self._record_lineup_player_stats(result.match_id, away_lineup_id, result.away_goals)
                self._stats(match['competition_id'], match['home_club_id'], match['away_club_id'], result.home_goals, result.away_goals)
                self.persist_advanced_stats(result.match_id, result.seed)
        except Exception:
            if managed_transaction:
                self.connection.rollback()
            raise
        return result

    def play(self, match_id: int, home_strength: int = 70, away_strength: int = 65, seed: int | None = None, home_lineup_id: int | None = None, away_lineup_id: int | None = None, managed_transaction: bool = True, home_form: int = 0, away_form: int = 0, home_morale: int = 0, away_morale: int = 0, home_tactic: int = 0, away_tactic: int = 0) -> MatchResult:
        result = self.generate_result(match_id, home_strength, away_strength, seed, home_form, away_form, home_morale, away_morale, home_tactic, away_tactic)
        return self.apply_result(result, home_lineup_id, away_lineup_id, managed_transaction)

    def postpone(self, match_id: int, new_match_date: str | None = None, managed_transaction: bool = True) -> None:
        self._require_match(match_id)
        if new_match_date is not None:
            date.fromisoformat(new_match_date)
        with self.transaction(managed_transaction):
            self.connection.execute('UPDATE matches SET status=?,match_date=? WHERE match_id=?', ('POSTPONED', new_match_date or self.connection.execute('SELECT match_date FROM matches WHERE match_id=?', (match_id,)).fetchone()[0], match_id))

    def reschedule(self, match_id: int, new_match_date: str, managed_transaction: bool = True) -> None:
        date.fromisoformat(new_match_date)
        match = self.connection.execute('SELECT status FROM matches WHERE match_id=?', (match_id,)).fetchone()
        if match is None:
            raise KeyError(f'MATCH_NOT_FOUND:{match_id}')
        if match['status'] == 'PLAYED':
            raise ValueError('ALREADY_PLAYED')
        with self.transaction(managed_transaction):
            self.connection.execute('UPDATE matches SET match_date=?,status=? WHERE match_id=?', (new_match_date, 'SCHEDULED', match_id))

    def record_event(self, match_id: int, event_type: str, minute: int, player_id: int | None = None, payload: dict | None = None) -> dict:
        match = self._require_match(match_id)
        if not str(event_type).strip() or not 0 <= int(minute) <= 130: raise ValueError('MATCH_EVENT_INVALID')
        previous = self.connection.execute('SELECT minute,event_id FROM match_events WHERE match_id=? ORDER BY event_id DESC LIMIT 1', (int(match_id),)).fetchone()
        if previous is not None and int(minute) < int(previous['minute'] or 0): raise ValueError('MATCH_EVENT_OUT_OF_ORDER')
        cur = self.connection.execute('INSERT INTO match_events(match_id,event_type,minute,player_id,payload) VALUES(?,?,?,?,?)', (int(match_id), str(event_type).strip(), int(minute), player_id, json.dumps(payload or {}, sort_keys=True, separators=(',', ':'))))
        self.connection.commit()
        return dict(self.connection.execute('SELECT * FROM match_events WHERE event_id=?', (cur.lastrowid,)).fetchone())

    def match_events(self, match_id: int) -> list[dict]:
        rows = self.connection.execute('SELECT * FROM match_events WHERE match_id=? ORDER BY minute,event_id', (int(match_id),)).fetchall()
        return [dict(row) for row in rows]

    def persist_advanced_stats(self, match_id: int, seed: int | None = None) -> dict:
        match=self.connection.execute('SELECT * FROM matches WHERE match_id=?',(int(match_id),)).fetchone()
        if not match: raise KeyError(f'MATCH_NOT_FOUND:{match_id}')
        rng=random.Random(seed if seed is not None else match['seed'] or match_id)
        values={'home_duels':rng.randint(25,70),'away_duels':rng.randint(25,70),'home_set_pieces':rng.randint(1,12),'away_set_pieces':rng.randint(1,12),'home_corners':rng.randint(0,12),'away_corners':rng.randint(0,12),'home_tactical_fouls':rng.randint(0,10),'away_tactical_fouls':rng.randint(0,10),'home_conditional_subs':rng.randint(0,5),'away_conditional_subs':rng.randint(0,5),'interval_plan':json.dumps({'home':'PRESS_AFTER_LOSS','away':'LOW_BLOCK'},sort_keys=True)}
        with self.connection: self.connection.execute('INSERT OR REPLACE INTO match_advanced_stats(match_id,home_duels,away_duels,home_set_pieces,away_set_pieces,home_corners,away_corners,home_tactical_fouls,away_tactical_fouls,home_conditional_subs,away_conditional_subs,interval_plan) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(match_id,*values.values()))
        return {'match_id':int(match_id),**values,'persisted':True}

    def advanced_preview(self, match_id: int, seed: int | None = None) -> dict:
        row=self.connection.execute('SELECT * FROM match_advanced_stats WHERE match_id=?',(int(match_id),)).fetchone()
        if row: return {**dict(row),'persisted':False}
        rng=random.Random(seed if seed is not None else match_id)
        return {'match_id':int(match_id),'home_duels':rng.randint(25,70),'away_duels':rng.randint(25,70),'home_set_pieces':rng.randint(1,12),'away_set_pieces':rng.randint(1,12),'persisted':False}

    def preview_result(self, match_id: int, home_strength: int = 70, away_strength: int = 65, seed: int | None = None) -> dict:
        match = self._require_match(match_id)
        result = self.generate_result(match_id, home_strength, away_strength, seed, persist=False)
        self.connection.rollback()
        return {'match_id': int(match['match_id']), 'home_goals': result.home_goals, 'away_goals': result.away_goals, 'seed': result.seed, 'persisted': False}

    def configure_match_conditions(self, match_id: int, crowd_effect: int = 0, weather_effect: int = 0, referee_profile: str = 'STANDARD', var_enabled: bool = False) -> dict:
        if not -20 <= int(crowd_effect) <= 20 or not -20 <= int(weather_effect) <= 20: raise ValueError('MATCH_CONDITION_INVALID')
        with self.connection: self.connection.execute('INSERT OR REPLACE INTO match_conditions(match_id,crowd_effect,weather_effect,referee_profile,var_enabled,updated_at) VALUES(?,?,?,?,?,?)',(match_id,crowd_effect,weather_effect,referee_profile,int(var_enabled),date.today().isoformat()))
        return dict(self.connection.execute('SELECT * FROM match_conditions WHERE match_id=?',(match_id,)).fetchone())

    def register_discipline(self, player_id: int, yellow: int = 0, red: int = 0) -> dict:
        if int(yellow)<0 or int(red)<0: raise ValueError('DISCIPLINE_INVALID')
        with self.connection: self.connection.execute('INSERT INTO disciplinary_accumulation(player_id,yellow_cards,red_cards,suspension_matches) VALUES(?,?,?,?) ON CONFLICT(player_id) DO UPDATE SET yellow_cards=yellow_cards+excluded.yellow_cards,red_cards=red_cards+excluded.red_cards,suspension_matches=suspension_matches+CASE WHEN excluded.red_cards>0 THEN 1 ELSE 0 END',(player_id,yellow,red,1 if int(red)>0 else 0))
        return dict(self.connection.execute('SELECT * FROM disciplinary_accumulation WHERE player_id=?',(player_id,)).fetchone())

    def review_event(self, match_id: int, event_id: int, action: str, reason: str) -> dict:
        if action not in ('ANNUL','CONFIRM') or not str(reason).strip(): raise ValueError('EVENT_REVIEW_INVALID')
        with self.connection: self.connection.execute('INSERT OR IGNORE INTO match_event_reviews(match_id,event_id,action,reason,created_at) VALUES(?,?,?,?,?)',(match_id,event_id,action,reason,date.today().isoformat()))
        row=self.connection.execute('SELECT * FROM match_event_reviews WHERE match_id=? AND event_id=?',(match_id,event_id)).fetchone(); return dict(row)

    def fatigue_by_minute(self, match_id: int, minute: int) -> dict:
        if int(minute)<0 or int(minute)>130: raise ValueError('MINUTE_INVALID')
        return {'match_id':int(match_id),'minute':int(minute),'home_fatigue':min(100,int(minute*.55)),'away_fatigue':min(100,int(minute*.6)),'persisted':False}

    def post_match_report(self, match_id: int, recovery_days: int = 2, staff_notes: str = '') -> dict:
        match=self.connection.execute("SELECT status FROM matches WHERE match_id=?",(match_id,)).fetchone()
        if not match or match['status']!='PLAYED': raise ValueError('RESULT_NOT_OFFICIAL')
        if int(recovery_days)<0: raise ValueError('RECOVERY_DAYS_INVALID')
        with self.connection: self.connection.execute('INSERT OR REPLACE INTO post_match_reports(match_id,recovery_days,staff_notes,created_at) VALUES(?,?,?,?)',(match_id,recovery_days,staff_notes,date.today().isoformat()))
        return dict(self.connection.execute('SELECT * FROM post_match_reports WHERE match_id=?',(match_id,)).fetchone())

    def result_audit(self, match_id: int) -> dict:
        match=self.connection.execute('SELECT match_id,status,home_goals,away_goals,seed FROM matches WHERE match_id=?',(match_id,)).fetchone()
        if not match: raise KeyError(match_id)
        stats=self.connection.execute('SELECT * FROM match_stats WHERE match_id=?',(match_id,)).fetchone()
        advanced=self.connection.execute('SELECT * FROM match_advanced_stats WHERE match_id=?',(match_id,)).fetchone()
        individual=self.connection.execute('SELECT * FROM player_match_stats WHERE match_id=? ORDER BY player_id',(match_id,)).fetchall()
        return {'match':dict(match),'stats':dict(stats) if stats else None,'advanced':dict(advanced) if advanced else None,'individual':[dict(row) for row in individual],'persisted':True}

    def official_summary(self, match_id: int) -> dict:
        match = self.connection.execute('SELECT * FROM matches WHERE match_id=?', (int(match_id),)).fetchone()
        if match is None: raise KeyError(f'MATCH_NOT_FOUND:{match_id}')
        if match['status'] != 'PLAYED': raise ValueError('RESULT_NOT_OFFICIAL')
        stats = self.connection.execute('SELECT * FROM match_stats WHERE match_id=?', (int(match_id),)).fetchone()
        return {'match': dict(match), 'stats': dict(stats) if stats else None, 'events': self.match_events(match_id), 'official': True}

    def reprocess_result(self, match_id: int, reason: str, seed: int | None = None) -> dict:
        match = self.connection.execute('SELECT * FROM matches WHERE match_id=?', (int(match_id),)).fetchone()
        if match is None: raise KeyError(f'MATCH_NOT_FOUND:{match_id}')
        if match['status'] != 'PLAYED': raise ValueError('RESULT_NOT_OFFICIAL')
        if not str(reason).strip(): raise ValueError('REPROCESS_REASON_REQUIRED')
        result = MatchResult(int(match_id), int(match['home_goals'] or 0), int(match['away_goals'] or 0), seed if seed is not None else match['seed'])
        with self.connection:
            cur=self.connection.execute('INSERT OR IGNORE INTO match_reprocess_audit(match_id,reason,seed,created_at) VALUES(?,?,?,?)',(int(match_id),str(reason).strip(),result.seed,date.today().isoformat()))
            if cur.rowcount:
                self.connection.execute('INSERT INTO match_events(match_id,event_type,minute,player_id,payload) VALUES(?,?,?,?,?)', (int(match_id), 'REPROCESS_AUDIT', 0, None, json.dumps({'reason': str(reason).strip(), 'seed': result.seed}, sort_keys=True)))
        return {'match_id': int(match_id), 'status': 'REPROCESS_REQUESTED' if cur.rowcount else 'ALREADY_REQUESTED', 'reason': str(reason).strip(), 'result': result}

    def score_distribution(self, season_id: int) -> list[dict[str, int]]:
        rows = self.connection.execute('''SELECT home_goals,away_goals,COUNT(*) AS matches FROM matches WHERE season_id=? AND status='PLAYED' GROUP BY home_goals,away_goals ORDER BY home_goals,away_goals''', (season_id,)).fetchall()
        return [dict(row) for row in rows]

    def _record_lineup_player_stats(self, match_id: int, lineup_id: int | None, goals: int) -> None:
        if lineup_id is None:
            return
        players = self.connection.execute('SELECT player_id FROM lineup_players WHERE lineup_id=? ORDER BY player_id', (lineup_id,)).fetchall()
        if not players:
            return
        for index, player in enumerate(players):
            player_goals = 1 if index < int(goals) else 0
            assists = 1 if index == 0 and int(goals) > 0 else 0
            self.connection.execute('''INSERT INTO player_match_stats(match_id,player_id,minutes,goals,assists,cards,rating)
                SELECT ?, ?, 90, ?, ?, 0, 7.0
                WHERE NOT EXISTS (SELECT 1 FROM player_match_stats WHERE match_id=? AND player_id=?)''',
                (match_id, player['player_id'], player_goals, assists, match_id, player['player_id']))

    def _stats(self, cid: int, home: int, away: int, hg: int, ag: int) -> None:
        for club, gf, ga in ((home, hg, ag), (away, ag, hg)):
            win = gf > ga
            draw = gf == ga
            self.connection.execute('''UPDATE team_competition_stats SET played=played+1,wins=wins+?,draws=draws+?,losses=losses+?,goals_for=goals_for+?,goals_against=goals_against+?,points=points+? WHERE competition_id=? AND club_id=?''', (int(win), int(draw), int(not win and not draw), gf, ga, 3 if win else 1 if draw else 0, cid, club))

    def standings(self, cid: int):
        return self.connection.execute('SELECT *,(goals_for-goals_against) AS goal_difference FROM team_competition_stats WHERE competition_id=? ORDER BY points DESC,wins DESC,goal_difference DESC,goals_for DESC', (cid,)).fetchall()

    def close(self):
        self.connection.close()
