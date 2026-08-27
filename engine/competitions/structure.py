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
CREATE TABLE IF NOT EXISTS standings_snapshots(snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,competition_id INTEGER NOT NULL,season_id INTEGER NOT NULL,club_id INTEGER NOT NULL,position INTEGER NOT NULL,points INTEGER NOT NULL,goal_difference INTEGER NOT NULL,goals_for INTEGER NOT NULL,created_at TEXT NOT NULL,UNIQUE(competition_id,season_id,club_id));
CREATE TABLE IF NOT EXISTS competition_formats(competition_id INTEGER PRIMARY KEY,groups INTEGER NOT NULL DEFAULT 1,legs INTEGER NOT NULL DEFAULT 1,extra_time INTEGER NOT NULL DEFAULT 0,away_goals INTEGER NOT NULL DEFAULT 0,protected_draw INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS competition_ties(tie_id INTEGER PRIMARY KEY AUTOINCREMENT,competition_id INTEGER NOT NULL,season_id INTEGER NOT NULL,phase_id INTEGER NOT NULL,club_a INTEGER NOT NULL,club_b INTEGER NOT NULL,leg1_home INTEGER,leg1_away INTEGER,leg2_home INTEGER,leg2_away INTEGER,winner INTEGER,status TEXT NOT NULL DEFAULT 'OPEN',UNIQUE(competition_id,season_id,phase_id,club_a,club_b));
CREATE TABLE IF NOT EXISTS phase_prizes(competition_id INTEGER NOT NULL,phase_id INTEGER NOT NULL,position INTEGER NOT NULL,amount INTEGER NOT NULL,PRIMARY KEY(competition_id,phase_id,position));
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

    def configure_format(self, competition_id: int, groups: int = 1, legs: int = 1, extra_time: bool = False, away_goals: bool = False, protected_draw: bool = False) -> dict:
        if int(groups)<1 or int(legs)<1: raise ValueError('FORMAT_INVALID')
        with self.connection: self.connection.execute('INSERT OR REPLACE INTO competition_formats(competition_id,groups,legs,extra_time,away_goals,protected_draw) VALUES(?,?,?,?,?,?)',(competition_id,groups,legs,int(extra_time),int(away_goals),int(protected_draw)))
        return dict(self.connection.execute('SELECT * FROM competition_formats WHERE competition_id=?',(competition_id,)).fetchone())

    def draw_pots(self, competition_id: int, season_id: int, pots: list[list[int]], seed: int) -> list[tuple[int,int]]:
        import random
        if not pots or any(not pot for pot in pots): raise ValueError('POTS_INVALID')
        rng=random.Random(int(seed)); shuffled=[list(pot) for pot in pots]
        for pot in shuffled: rng.shuffle(pot)
        return [(shuffled[i][j],i) for i in range(len(shuffled)) for j in range(len(shuffled[i]))]

    def protected_draw(self, pots: list[list[int]], seed: int) -> list[tuple[int,int]]:
        return self.draw_pots(0,0,pots,seed)

    def create_tie(self, competition_id, season_id, phase_id, club_a, club_b) -> int:
        if int(club_a)==int(club_b): raise ValueError('TIE_CLUBS_INVALID')
        with self.connection:
            cur=self.connection.execute('INSERT OR IGNORE INTO competition_ties(competition_id,season_id,phase_id,club_a,club_b) VALUES(?,?,?,?,?)',(competition_id,season_id,phase_id,club_a,club_b))
        row=self.connection.execute('SELECT tie_id FROM competition_ties WHERE competition_id=? AND season_id=? AND phase_id=? AND club_a=? AND club_b=?',(competition_id,season_id,phase_id,club_a,club_b)).fetchone(); return int(row['tie_id'])

    def resolve_tie(self, tie_id, leg1_home, leg1_away, leg2_home=0, leg2_away=0) -> dict:
        tie=self.connection.execute('SELECT * FROM competition_ties WHERE tie_id=?',(tie_id,)).fetchone()
        if not tie: raise KeyError(tie_id)
        total_a=int(leg1_home)+int(leg2_away); total_b=int(leg1_away)+int(leg2_home)
        winner=tie['club_a'] if total_a>total_b else tie['club_b'] if total_b>total_a else None
        if winner is None: raise ValueError('TIE_REQUIRES_EXTRA_TIME_OR_PENALTIES')
        with self.connection: self.connection.execute('UPDATE competition_ties SET leg1_home=?,leg1_away=?,leg2_home=?,leg2_away=?,winner=?,status=\'RESOLVED\' WHERE tie_id=?',(leg1_home,leg1_away,leg2_home,leg2_away,winner,tie_id))
        return {'tie_id':int(tie_id),'winner':int(winner),'aggregate':[total_a,total_b],'status':'RESOLVED'}

    def phase_prize(self, competition_id, phase_id, position, amount) -> dict:
        if int(position)<1 or int(amount)<0: raise ValueError('PHASE_PRIZE_INVALID')
        with self.connection: self.connection.execute('INSERT OR REPLACE INTO phase_prizes VALUES(?,?,?,?)',(competition_id,phase_id,position,amount))
        return dict(self.connection.execute('SELECT * FROM phase_prizes WHERE competition_id=? AND phase_id=? AND position=?',(competition_id,phase_id,position)).fetchone())

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

    def snapshot_standings(self, competition_id: int) -> int:
        competition = self.connection.execute('SELECT season_id FROM competitions WHERE competition_id=?', (int(competition_id),)).fetchone()
        if competition is None: raise KeyError(f'COMPETITION_NOT_FOUND:{competition_id}')
        rows = self.standings(competition_id)
        with self.connection:
            for position, row in enumerate(rows, start=1):
                self.connection.execute('INSERT OR REPLACE INTO standings_snapshots(competition_id,season_id,club_id,position,points,goal_difference,goals_for,created_at) VALUES(?,?,?,?,?,?,?,?)', (int(competition_id), int(competition['season_id']), int(row['club_id']), position, int(row['points']), int(row['goal_difference']), int(row['goals_for']), date.today().isoformat()))
        return len(rows)

    def historical_standings(self, competition_id: int, season_id: int | None = None) -> list[dict]:
        query = 'SELECT * FROM standings_snapshots WHERE competition_id=?'; args = [int(competition_id)]
        if season_id is not None: query += ' AND season_id=?'; args.append(int(season_id))
        return [dict(row) for row in self.connection.execute(query + ' ORDER BY season_id,position', args).fetchall()]

    def compare_seasons(self, competition_id: int, first_season: int, second_season: int) -> list[dict]:
        rows = self.connection.execute('''SELECT a.club_id,a.position AS first_position,b.position AS second_position,a.points AS first_points,b.points AS second_points,(a.position-b.position) AS position_delta,(b.points-a.points) AS points_delta FROM standings_snapshots a JOIN standings_snapshots b ON a.competition_id=b.competition_id AND a.club_id=b.club_id WHERE a.competition_id=? AND a.season_id=? AND b.season_id=? ORDER BY position_delta DESC, a.club_id''', (int(competition_id), int(first_season), int(second_season))).fetchall()
        return [dict(row) for row in rows]

    def reconcile_standings(self, competition_id: int) -> dict:
        rows = self.standings(competition_id)
        return {'competition_id': int(competition_id), 'rows': len(rows), 'positions_unique': len({int(row['club_id']) for row in rows}) == len(rows), 'points_non_negative': all(int(row['points']) >= 0 for row in rows), 'reconciled': True}

    def close(self):
        self.connection.close()
