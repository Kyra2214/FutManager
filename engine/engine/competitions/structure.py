from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from engine.core.state_store import assert_mutable_state_path

SCHEMA = '''
CREATE TABLE IF NOT EXISTS competition_phases(phase_id INTEGER PRIMARY KEY AUTOINCREMENT,competition_id INTEGER NOT NULL,name TEXT NOT NULL,order_no INTEGER NOT NULL,type TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'PLANNED',UNIQUE(competition_id,order_no));
CREATE TABLE IF NOT EXISTS competition_rounds(round_id INTEGER PRIMARY KEY AUTOINCREMENT,phase_id INTEGER NOT NULL,number INTEGER NOT NULL,round_date TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'PLANNED',UNIQUE(phase_id,number));
CREATE TABLE IF NOT EXISTS fixtures(fixture_id INTEGER PRIMARY KEY AUTOINCREMENT,competition_id INTEGER NOT NULL,season_id INTEGER NOT NULL,phase_id INTEGER NOT NULL,round_id INTEGER NOT NULL,home_club_id INTEGER NOT NULL,away_club_id INTEGER NOT NULL,scheduled_at TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'SCHEDULED',match_id INTEGER,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,UNIQUE(competition_id,season_id,round_id,home_club_id,away_club_id));
CREATE TABLE IF NOT EXISTS competition_config(competition_id INTEGER PRIMARY KEY,win_points INTEGER NOT NULL DEFAULT 3,draw_points INTEGER NOT NULL DEFAULT 1,loss_points INTEGER NOT NULL DEFAULT 0,turns INTEGER NOT NULL DEFAULT 1,tiebreakers TEXT NOT NULL DEFAULT 'points,wins,goal_difference,goals_for',penalty_shootout_enabled INTEGER NOT NULL DEFAULT 0,promotion_slots INTEGER NOT NULL DEFAULT 0,relegation_slots INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS competition_champions(competition_id INTEGER NOT NULL,season_id INTEGER NOT NULL,champion_club_id INTEGER NOT NULL,finalized_at TEXT NOT NULL,PRIMARY KEY(competition_id,season_id));
CREATE TABLE IF NOT EXISTS competition_prizes(competition_id INTEGER NOT NULL,position INTEGER NOT NULL,amount INTEGER NOT NULL CHECK(amount >= 0),PRIMARY KEY(competition_id,position));
CREATE TABLE IF NOT EXISTS competition_prize_payments(competition_id INTEGER NOT NULL,season_id INTEGER NOT NULL,club_id INTEGER NOT NULL,position INTEGER NOT NULL,amount INTEGER NOT NULL,paid_at TEXT NOT NULL,PRIMARY KEY(competition_id,season_id,club_id,position));
CREATE TABLE IF NOT EXISTS competition_transitions(competition_id INTEGER NOT NULL,season_id INTEGER NOT NULL,club_id INTEGER NOT NULL,direction TEXT NOT NULL CHECK(direction IN ('PROMOTED','RELEGATED')),position INTEGER NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(competition_id,season_id,club_id,direction));
CREATE TABLE IF NOT EXISTS classification_alerts(alert_id INTEGER PRIMARY KEY AUTOINCREMENT,competition_id INTEGER NOT NULL,season_id INTEGER NOT NULL,club_id INTEGER NOT NULL,alert_type TEXT NOT NULL,message TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(competition_id,season_id,club_id,alert_type));
'''


@dataclass(frozen=True)
class Fixture:
    fixture_id: int
    competition_id: int
    round_id: int
    home_club_id: int
    away_club_id: int
    scheduled_at: str
    status: str


class CompetitionStructureService:
    def __init__(self, db: str | Path | sqlite3.Connection):
        if isinstance(db, sqlite3.Connection):
            self.connection = db
        else:
            assert_mutable_state_path(db)
            self.connection = sqlite3.connect(str(db))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.executescript(SCHEMA)
        self._ensure_config_columns()
        self.connection.commit()

    def _ensure_config_columns(self) -> None:
        existing = {row[1] for row in self.connection.execute('PRAGMA table_info(competition_config)')}
        definitions = {
            'penalty_shootout_enabled': 'INTEGER NOT NULL DEFAULT 0',
            'promotion_slots': 'INTEGER NOT NULL DEFAULT 0',
            'relegation_slots': 'INTEGER NOT NULL DEFAULT 0',
        }
        for name, definition in definitions.items():
            if name not in existing:
                self.connection.execute(f'ALTER TABLE competition_config ADD COLUMN {name} {definition}')

    def add_phase(self, competition_id: int, name: str = 'REGULAR_SEASON', order_no: int = 1, type_: str = 'LEAGUE_TABLE') -> int:
        cur = self.connection.execute('INSERT INTO competition_phases(competition_id,name,order_no,type) VALUES(?,?,?,?)', (competition_id, name, order_no, type_))
        self.connection.commit()
        return int(cur.lastrowid)

    def add_round(self, phase_id: int, number: int, round_date: str, status: str = 'PLANNED') -> int:
        date.fromisoformat(round_date)
        cur = self.connection.execute('INSERT INTO competition_rounds(phase_id,number,round_date,status) VALUES(?,?,?,?)', (phase_id, number, round_date, status))
        self.connection.commit()
        return int(cur.lastrowid)

    def generate_fixtures(self, competition_id: int, phase_id: int, season_id: int, club_ids: list[int], start_date: str = '2026-01-10', turns: int = 1) -> list[int]:
        if len(club_ids) < 2:
            raise ValueError('AT_LEAST_TWO_CLUBS_REQUIRED')
        if turns < 1:
            raise ValueError('TURNS_REQUIRED')
        ids = list(dict.fromkeys(club_ids))
        day = date.fromisoformat(start_date)
        created: list[int] = []
        round_no = 1
        for turn in range(turns):
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    home, away = (ids[i], ids[j]) if turn % 2 == 0 else (ids[j], ids[i])
                    round_id = self.add_round(phase_id, round_no, day.isoformat())
                    cur = self.connection.execute('''INSERT INTO fixtures(competition_id,season_id,phase_id,round_id,home_club_id,away_club_id,scheduled_at,created_at,updated_at)
                        VALUES(?,?,?,?,?,?,?,?,?)''', (competition_id, season_id, phase_id, round_id, home, away, day.isoformat(), date.today().isoformat(), date.today().isoformat()))
                    created.append(int(cur.lastrowid))
                    day += timedelta(days=7)
                    round_no += 1
        self.connection.commit()
        return created

    def calendar(self, competition_id: int, club_id: int | None = None):
        query = 'SELECT * FROM fixtures WHERE competition_id=?'
        args: list[object] = [competition_id]
        if club_id is not None:
            query += ' AND (home_club_id=? OR away_club_id=?)'
            args += [club_id, club_id]
        return self.connection.execute(query + ' ORDER BY scheduled_at', args).fetchall()

    def top_scorers(self, competition_id: int, limit: int = 20):
        return self.connection.execute('''SELECT p.player_id, SUM(p.goals) goals, SUM(p.assists) assists, SUM(p.minutes) minutes
            FROM player_match_stats p JOIN matches m ON m.match_id=p.match_id WHERE m.competition_id=? GROUP BY p.player_id
            ORDER BY goals DESC, assists DESC, minutes ASC LIMIT ?''', (competition_id, limit)).fetchall()

    def configure_rules(self, competition_id: int, *, win_points: int = 3, draw_points: int = 1, loss_points: int = 0, turns: int = 1, tiebreakers: str = 'points,wins,goal_difference,goals_for', penalty_shootout_enabled: bool = False, promotion_slots: int = 0, relegation_slots: int = 0) -> None:
        if min(win_points, draw_points, loss_points, turns, promotion_slots, relegation_slots) < 0 or turns < 1:
            raise ValueError('COMPETITION_RULES_INVALID')
        self.connection.execute('''INSERT INTO competition_config(competition_id,win_points,draw_points,loss_points,turns,tiebreakers,penalty_shootout_enabled,promotion_slots,relegation_slots)
            VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(competition_id) DO UPDATE SET win_points=excluded.win_points,draw_points=excluded.draw_points,
            loss_points=excluded.loss_points,turns=excluded.turns,tiebreakers=excluded.tiebreakers,penalty_shootout_enabled=excluded.penalty_shootout_enabled,
            promotion_slots=excluded.promotion_slots,relegation_slots=excluded.relegation_slots''', (competition_id, win_points, draw_points, loss_points, turns, tiebreakers, int(penalty_shootout_enabled), promotion_slots, relegation_slots))
        self.connection.commit()

    def resolve_penalty_shootout(self, match_id: int, home_penalties: int, away_penalties: int) -> str:
        if min(home_penalties, away_penalties) < 0 or home_penalties == away_penalties:
            raise ValueError('PENALTY_RESULT_INVALID')
        match = self.connection.execute('SELECT competition_id FROM matches WHERE match_id=?', (match_id,)).fetchone()
        if match is None:
            raise KeyError(f'MATCH_NOT_FOUND:{match_id}')
        config = self.connection.execute('SELECT penalty_shootout_enabled FROM competition_config WHERE competition_id=?', (match['competition_id'],)).fetchone()
        if not config or not config['penalty_shootout_enabled']:
            raise ValueError('PENALTY_SHOOTOUT_NOT_ENABLED')
        winner = 'HOME' if home_penalties > away_penalties else 'AWAY'
        self.connection.execute('INSERT INTO match_events(match_id,event_type,minute,player_id,payload) VALUES(?,?,?,?,?)', (match_id, 'PENALTY_SHOOTOUT', 120, None, json.dumps({'home': home_penalties, 'away': away_penalties, 'winner': winner}, sort_keys=True)))
        self.connection.commit()
        return winner

    def standings(self, competition_id: int):
        return self.connection.execute('''SELECT *, (goals_for-goals_against) AS goal_difference FROM team_competition_stats
            WHERE competition_id=? ORDER BY points DESC,wins DESC,goal_difference DESC,goals_for DESC,club_id''', (competition_id,)).fetchall()

    def finish_competition(self, competition_id: int) -> bool:
        pending = self.connection.execute("SELECT COUNT(*) FROM fixtures WHERE competition_id=? AND status IN ('SCHEDULED','POSTPONED')", (competition_id,)).fetchone()[0]
        if pending:
            raise ValueError('PENDING_FIXTURES')
        row = self.connection.execute('SELECT season_id,status FROM competitions WHERE competition_id=?', (competition_id,)).fetchone()
        if row is None:
            raise KeyError(f'COMPETITION_NOT_FOUND:{competition_id}')
        if row['status'] == 'FINISHED':
            return False
        self.connection.execute("UPDATE competitions SET status='FINISHED' WHERE competition_id=?", (competition_id,))
        standings = self.standings(competition_id)
        if standings:
            self.connection.execute('INSERT OR IGNORE INTO competition_champions(competition_id,season_id,champion_club_id,finalized_at) VALUES(?,?,?,?)', (competition_id, row['season_id'], standings[0]['club_id'], date.today().isoformat()))
        self.connection.commit()
        return True

    def set_prizes(self, competition_id: int, prizes_by_position: dict[int, int]) -> None:
        if any(position < 1 or amount < 0 for position, amount in prizes_by_position.items()):
            raise ValueError('PRIZES_INVALID')
        for position, amount in prizes_by_position.items():
            self.connection.execute('INSERT OR REPLACE INTO competition_prizes(competition_id,position,amount) VALUES(?,?,?)', (competition_id, position, amount))
        self.connection.commit()

    def award_prizes(self, competition_id: int) -> int:
        competition = self.connection.execute('SELECT season_id,status FROM competitions WHERE competition_id=?', (competition_id,)).fetchone()
        if competition is None:
            raise KeyError(f'COMPETITION_NOT_FOUND:{competition_id}')
        if competition['status'] != 'FINISHED':
            raise ValueError('COMPETITION_NOT_FINISHED')
        paid = 0
        for position, amount in self.connection.execute('SELECT position,amount FROM competition_prizes WHERE competition_id=?', (competition_id,)).fetchall():
            standings = self.standings(competition_id)
            if position > len(standings):
                continue
            club_id = standings[position - 1]['club_id']
            cur = self.connection.execute('INSERT OR IGNORE INTO competition_prize_payments(competition_id,season_id,club_id,position,amount,paid_at) VALUES(?,?,?,?,?,?)', (competition_id, competition['season_id'], club_id, position, amount, date.today().isoformat()))
            paid += int(cur.rowcount == 1)
        self.connection.commit()
        return paid

    def record_transitions(self, competition_id: int, promoted_club_ids: list[int], relegated_club_ids: list[int]) -> int:
        competition = self.connection.execute('SELECT season_id FROM competitions WHERE competition_id=?', (competition_id,)).fetchone()
        if competition is None:
            raise KeyError(f'COMPETITION_NOT_FOUND:{competition_id}')
        config = self.connection.execute('SELECT promotion_slots,relegation_slots FROM competition_config WHERE competition_id=?', (competition_id,)).fetchone()
        if config is None:
            raise ValueError('COMPETITION_RULES_NOT_CONFIGURED')
        if len(promoted_club_ids) > config['promotion_slots'] or len(relegated_club_ids) > config['relegation_slots']:
            raise ValueError('TRANSITION_LIMIT_EXCEEDED')
        inserted = 0
        for direction, clubs in (('PROMOTED', promoted_club_ids), ('RELEGATED', relegated_club_ids)):
            for position, club_id in enumerate(clubs, start=1):
                cur = self.connection.execute('INSERT OR IGNORE INTO competition_transitions(competition_id,season_id,club_id,direction,position,created_at) VALUES(?,?,?,?,?,?)', (competition_id, competition['season_id'], club_id, direction, position, date.today().isoformat()))
                inserted += int(cur.rowcount == 1)
        self.connection.commit()
        return inserted

    def emit_classification_alerts(self, competition_id: int) -> int:
        competition = self.connection.execute('SELECT season_id FROM competitions WHERE competition_id=?', (competition_id,)).fetchone()
        if competition is None:
            raise KeyError(f'COMPETITION_NOT_FOUND:{competition_id}')
        standings = self.standings(competition_id)
        inserted = 0
        if standings:
            candidates = [(standings[0]['club_id'], 'LEADER', 'Clube lidera a classificação')]
            if len(standings) > 1:
                candidates.append((standings[-1]['club_id'], 'BOTTOM', 'Clube ocupa a última posição'))
            for club_id, alert_type, message in candidates:
                cur = self.connection.execute('INSERT OR IGNORE INTO classification_alerts(competition_id,season_id,club_id,alert_type,message,created_at) VALUES(?,?,?,?,?,?)', (competition_id, competition['season_id'], club_id, alert_type, message, date.today().isoformat()))
                inserted += int(cur.rowcount == 1)
        self.connection.commit()
        return inserted

    def close(self):
        self.connection.close()
