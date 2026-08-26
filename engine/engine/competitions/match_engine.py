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
