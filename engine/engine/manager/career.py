from __future__ import annotations

from datetime import date, datetime, timezone
from enum import StrEnum
import json
import sqlite3
import hashlib
from typing import Any

from engine.core.schema import ensure_schema_version
from engine.core.state_store import assert_mutable_state_path, configure_state_connection
from engine.world.first_division import FIRST_DIVISION_SOURCES, resolve_first_division_members

SCHEMA = '''
CREATE TABLE IF NOT EXISTS managers(manager_id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,nationality TEXT,age INTEGER NOT NULL,reputation INTEGER NOT NULL DEFAULT 0,experience INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'ACTIVE',created_at TEXT NOT NULL,current_club_id INTEGER,active_career INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS manager_careers(career_id INTEGER PRIMARY KEY AUTOINCREMENT,manager_id INTEGER NOT NULL UNIQUE,name TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,season_id INTEGER,current_club_id INTEGER,status TEXT NOT NULL DEFAULT 'ACTIVE',engine_version TEXT NOT NULL DEFAULT '1.0',starting_division INTEGER NOT NULL DEFAULT 4);
CREATE TABLE IF NOT EXISTS manager_contracts(manager_contract_id INTEGER PRIMARY KEY AUTOINCREMENT,manager_id INTEGER NOT NULL,club_id INTEGER NOT NULL,start_date TEXT NOT NULL,end_date TEXT NOT NULL,salary INTEGER NOT NULL,bonus INTEGER NOT NULL DEFAULT 0,objective TEXT,status TEXT NOT NULL DEFAULT 'ACTIVE');
CREATE TABLE IF NOT EXISTS manager_objectives(objective_id INTEGER PRIMARY KEY AUTOINCREMENT,career_id INTEGER NOT NULL,type TEXT NOT NULL,priority INTEGER NOT NULL,deadline TEXT,status TEXT NOT NULL DEFAULT 'ACTIVE',progress REAL NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS manager_history(history_id INTEGER PRIMARY KEY AUTOINCREMENT,manager_id INTEGER NOT NULL,club_id INTEGER,event_type TEXT NOT NULL,event_date TEXT NOT NULL,payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS manager_inbox(message_id INTEGER PRIMARY KEY AUTOINCREMENT,manager_id INTEGER NOT NULL,type TEXT NOT NULL,title TEXT NOT NULL,body TEXT,reference TEXT UNIQUE,read INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS manager_job_offers(offer_id INTEGER PRIMARY KEY AUTOINCREMENT,manager_id INTEGER NOT NULL,club_id INTEGER NOT NULL,salary INTEGER NOT NULL,duration INTEGER NOT NULL,objective TEXT,reputation_min INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'OFFERED');
CREATE TABLE IF NOT EXISTS manager_selection_assignments(selection_assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,manager_id INTEGER NOT NULL UNIQUE,career_id INTEGER NOT NULL UNIQUE,selection_id INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'ACTIVE',appointed_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS manager_preferences(preference_id INTEGER PRIMARY KEY AUTOINCREMENT,manager_id INTEGER NOT NULL,preference_key TEXT NOT NULL,preference_value TEXT NOT NULL,updated_at TEXT NOT NULL,UNIQUE(manager_id,preference_key));
CREATE TABLE IF NOT EXISTS career_snapshots(snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,career_id INTEGER NOT NULL,manager_id INTEGER NOT NULL,created_at TEXT NOT NULL,engine_version TEXT NOT NULL,payload TEXT NOT NULL,UNIQUE(career_id,created_at));
CREATE TABLE IF NOT EXISTS migration_audit(audit_id INTEGER PRIMARY KEY AUTOINCREMENT,component TEXT NOT NULL,version INTEGER NOT NULL,applied_at TEXT NOT NULL,content_hash TEXT NOT NULL,UNIQUE(component,version));
CREATE TABLE IF NOT EXISTS career_snapshot_audit(audit_id INTEGER PRIMARY KEY AUTOINCREMENT,snapshot_id INTEGER NOT NULL,career_id INTEGER NOT NULL,action TEXT NOT NULL,success INTEGER NOT NULL,details TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS manager_permission_audit(permission_audit_id INTEGER PRIMARY KEY AUTOINCREMENT,manager_id INTEGER NOT NULL,action TEXT NOT NULL,allowed INTEGER NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS career_change_audit(change_id INTEGER PRIMARY KEY AUTOINCREMENT,career_id INTEGER NOT NULL,manager_id INTEGER NOT NULL,origin_club_id INTEGER,destination_club_id INTEGER,created_at TEXT NOT NULL,reference TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS career_world_configs(career_id INTEGER PRIMARY KEY,manager_id INTEGER NOT NULL,combined_name TEXT NOT NULL,starting_division INTEGER NOT NULL DEFAULT 4,world_mode TEXT NOT NULL DEFAULT 'PARALLEL',created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS career_world_countries(career_id INTEGER NOT NULL,country_id INTEGER NOT NULL,country_name TEXT NOT NULL,country_code TEXT,PRIMARY KEY(career_id,country_id));
CREATE TABLE IF NOT EXISTS career_national_reassignments(career_id INTEGER PRIMARY KEY,manager_id INTEGER NOT NULL,club_id INTEGER NOT NULL,country_id INTEGER NOT NULL,original_division INTEGER NOT NULL,career_division INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'ACTIVE',created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS first_division_membership(country_id INTEGER NOT NULL,club_id INTEGER NOT NULL,source_name TEXT NOT NULL,source_url TEXT NOT NULL,season_label TEXT NOT NULL,imported_at TEXT NOT NULL,PRIMARY KEY(country_id,club_id));
CREATE TABLE IF NOT EXISTS career_parallel_leagues(career_id INTEGER PRIMARY KEY,manager_id INTEGER NOT NULL,name TEXT NOT NULL,season_id INTEGER,total_clubs INTEGER NOT NULL,source_country_count INTEGER NOT NULL,seed TEXT NOT NULL,division_count INTEGER NOT NULL DEFAULT 4,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS career_parallel_entries(career_id INTEGER NOT NULL,club_id INTEGER NOT NULL,origin_country_id INTEGER NOT NULL,origin_division INTEGER NOT NULL DEFAULT 1,parallel_division INTEGER NOT NULL,parallel_position INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'ACTIVE',PRIMARY KEY(career_id,club_id));
CREATE TABLE IF NOT EXISTS career_parallel_fixtures(fixture_id INTEGER PRIMARY KEY AUTOINCREMENT,career_id INTEGER NOT NULL,season_number INTEGER NOT NULL,matchday INTEGER NOT NULL,leg INTEGER NOT NULL,division INTEGER NOT NULL,scheduled_date TEXT NOT NULL,home_club_id INTEGER NOT NULL,away_club_id INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'SCHEDULED',home_goals INTEGER,away_goals INTEGER,played_at TEXT,UNIQUE(career_id,season_number,matchday,leg,home_club_id,away_club_id));
CREATE TABLE IF NOT EXISTS career_parallel_standings(career_id INTEGER NOT NULL,season_number INTEGER NOT NULL,club_id INTEGER NOT NULL,division INTEGER NOT NULL,played INTEGER NOT NULL DEFAULT 0,wins INTEGER NOT NULL DEFAULT 0,draws INTEGER NOT NULL DEFAULT 0,losses INTEGER NOT NULL DEFAULT 0,goals_for INTEGER NOT NULL DEFAULT 0,goals_against INTEGER NOT NULL DEFAULT 0,points INTEGER NOT NULL DEFAULT 0,position INTEGER NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(career_id,season_number,club_id));
CREATE TABLE IF NOT EXISTS career_parallel_season_closures(closure_id INTEGER PRIMARY KEY AUTOINCREMENT,career_id INTEGER NOT NULL,season_number INTEGER NOT NULL,closed_at TEXT NOT NULL,promoted_count INTEGER NOT NULL,relegated_count INTEGER NOT NULL,details TEXT NOT NULL,UNIQUE(career_id,season_number));
CREATE INDEX IF NOT EXISTS idx_parallel_fixtures_lookup ON career_parallel_fixtures(career_id,season_number,division,matchday,leg);
CREATE INDEX IF NOT EXISTS idx_parallel_standings_lookup ON career_parallel_standings(career_id,season_number,division,position);
CREATE INDEX IF NOT EXISTS idx_first_division_country ON first_division_membership(country_id,club_id);
CREATE INDEX IF NOT EXISTS idx_world_countries_career ON career_world_countries(career_id,country_id);
  '''


class ManagerStatus(StrEnum):
    ACTIVE = 'ACTIVE'
    RESIGNED = 'RESIGNED'
    TERMINATED = 'TERMINATED'


class ManagerService:
    ENGINE_VERSION = '1.1'

    def __init__(self, db: str | sqlite3.Connection):
        if not isinstance(db, sqlite3.Connection):
            assert_mutable_state_path(db)
        self.connection = sqlite3.connect(str(db)) if not isinstance(db, sqlite3.Connection) else db
        configure_state_connection(self.connection)
        self.connection.executescript(SCHEMA)
        career_columns = {row[1] for row in self.connection.execute('PRAGMA table_info(manager_careers)').fetchall()}
        if 'starting_division' not in career_columns:
            self.connection.execute('ALTER TABLE manager_careers ADD COLUMN starting_division INTEGER NOT NULL DEFAULT 4')
        world_config_columns = {row[1] for row in self.connection.execute('PRAGMA table_info(career_world_configs)').fetchall()}
        if 'world_mode' not in world_config_columns:
            self.connection.execute("ALTER TABLE career_world_configs ADD COLUMN world_mode TEXT NOT NULL DEFAULT 'PARALLEL'")
        fixture_columns = {row[1] for row in self.connection.execute('PRAGMA table_info(career_parallel_fixtures)').fetchall()}
        if 'scheduled_date' not in fixture_columns:
            self.connection.execute("ALTER TABLE career_parallel_fixtures ADD COLUMN scheduled_date TEXT NOT NULL DEFAULT '1970-01-01'")
        ensure_schema_version(self.connection)
        self.connection.execute(
            'INSERT OR IGNORE INTO migration_audit(component,version,applied_at,content_hash) VALUES(?,?,?,?)',
            ('manager_career', 3, self._now(), 'manager-career-schema-v3'),
        )
        self.connection.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _audit_permission(self, manager_id: int, action: str, allowed: bool, reason: str) -> None:
        self.connection.execute(
            'INSERT INTO manager_permission_audit(manager_id,action,allowed,reason,created_at) VALUES(?,?,?,?,?)',
            (manager_id, action, int(allowed), reason, self._now()),
        )

    def audit_constraints(self, career_id: int | None = None) -> dict[str, Any]:
        """Audita constraints SQLite e invariantes de carreira sem alterar o estado."""
        foreign_keys = int(self.connection.execute('PRAGMA foreign_keys').fetchone()[0])
        integrity_rows = self.connection.execute('PRAGMA integrity_check').fetchall()
        foreign_key_rows = self.connection.execute('PRAGMA foreign_key_check').fetchall()
        checks: dict[str, bool] = {
            'foreign_keys_enabled': foreign_keys == 1,
            'integrity_check': len(integrity_rows) == 1 and str(integrity_rows[0][0]).lower() == 'ok',
            'foreign_key_check': not foreign_key_rows,
        }
        params: tuple[Any, ...] = ()
        scope = ''
        if career_id is not None:
            scope = ' WHERE career_id=?'
            params = (career_id,)
        duplicate_entries = self.connection.execute(
            f'SELECT career_id,club_id,COUNT(*) FROM career_parallel_entries{scope} GROUP BY career_id,club_id HAVING COUNT(*) > 1', params
        ).fetchall()
        duplicate_fixtures = self.connection.execute(
            f'SELECT career_id,season_number,matchday,leg,home_club_id,away_club_id,COUNT(*) FROM career_parallel_fixtures{scope} GROUP BY career_id,season_number,matchday,leg,home_club_id,away_club_id HAVING COUNT(*) > 1', params
        ).fetchall()
        invalid_divisions = self.connection.execute(
            f'SELECT career_id,club_id,parallel_division FROM career_parallel_entries{scope} AND parallel_division NOT BETWEEN 1 AND 4' if scope else 'SELECT career_id,club_id,parallel_division FROM career_parallel_entries WHERE parallel_division NOT BETWEEN 1 AND 4',
            params,
        ).fetchall()
        checks.update({
            'unique_parallel_entries': not duplicate_entries,
            'unique_parallel_fixtures': not duplicate_fixtures,
            'valid_parallel_divisions': not invalid_divisions,
        })
        return {
            'status': 'VALID' if all(checks.values()) else 'INVALID',
            'career_id': career_id,
            'checks': checks,
            'violations': {
                'foreign_keys': foreign_key_rows,
                'duplicate_entries': duplicate_entries,
                'duplicate_fixtures': duplicate_fixtures,
                'invalid_divisions': invalid_divisions,
            },
        }

    def audit_indexes(self, career_id: int | None = None) -> dict[str, Any]:
        """Confirma índices de leitura sem executar mutações ou regras no frontend."""
        expected = {
            'idx_parallel_fixtures_lookup': 'career_parallel_fixtures',
            'idx_parallel_standings_lookup': 'career_parallel_standings',
            'idx_first_division_country': 'first_division_membership',
            'idx_world_countries_career': 'career_world_countries',
        }
        indexes: dict[str, bool] = {}
        for index_name, table_name in expected.items():
            rows = self.connection.execute(f'PRAGMA index_list({table_name})').fetchall()
            indexes[index_name] = any(str(row[1]) == index_name for row in rows)
        fixture_query = 'SELECT fixture_id FROM career_parallel_fixtures WHERE career_id=? AND season_number=? AND division=? AND matchday=? AND leg=?'
        standings_query = 'SELECT club_id FROM career_parallel_standings WHERE career_id=? AND season_number=? AND division=? ORDER BY position'
        fixture_plan = [tuple(row) for row in self.connection.execute('EXPLAIN QUERY PLAN ' + fixture_query, (career_id or 0, 1, 1, 1, 1)).fetchall()]
        standings_plan = [tuple(row) for row in self.connection.execute('EXPLAIN QUERY PLAN ' + standings_query, (career_id or 0, 1, 1)).fetchall()]
        plan_text = ' '.join(' '.join(map(str, row)) for row in fixture_plan + standings_plan).lower()
        checks = {
            'expected_indexes': all(indexes.values()),
            'fixture_query_plan_available': bool(fixture_plan),
            'standings_query_plan_available': bool(standings_plan),
            'query_plan_uses_index': 'idx_parallel_' in plan_text or 'autoindex' in plan_text,
        }
        return {'status': 'VALID' if all(checks.values()) else 'INVALID', 'career_id': career_id, 'indexes': indexes, 'checks': checks, 'plans': {'fixtures': fixture_plan, 'standings': standings_plan}}

    def create_manager(self, name: str, nationality: str | None, age: int) -> int:
        cur = self.connection.execute('INSERT INTO managers(name,nationality,age,created_at) VALUES(?,?,?,?)', (name, nationality, age, date.today().isoformat()))
        self.connection.commit()
        return int(cur.lastrowid)

    def _country_details(self, country_id: int) -> tuple[str, str | None]:
        try:
            row = self.connection.execute('SELECT nome,codigo FROM paises WHERE pais_id=?', (country_id,)).fetchone()
        except sqlite3.Error:
            row = None
        overrides = {29: ('Brasil', 'BRA'), 104: ('Itália', 'ITA'), 65: ('Espanha', 'ESP'), 154: ('Portugal', 'POR'), 97: ('Inglaterra', 'ENG'), 3: ('Alemanha', 'GER'), 72: ('França', 'FRA'), 11: ('Argentina', 'ARG'), 192: ('Turquia', 'TUR')}
        if row and row[0] and not str(row[0]).startswith('País ID'):
            return str(row[0]), row[1]
        return overrides.get(int(country_id), (f'País ID {country_id}', row[1] if row else None))

    def list_world_countries(self, search: str = '', limit: int = 48) -> list[dict[str, Any]]:
        search = (search or '').strip().lower()
        limit = min(max(int(limit), 1), 96)
        try:
            rows = self.connection.execute('SELECT pais_id,nome,codigo FROM paises ORDER BY CASE pais_id WHEN 29 THEN 0 WHEN 104 THEN 1 WHEN 65 THEN 2 WHEN 154 THEN 3 WHEN 97 THEN 4 WHEN 3 THEN 5 WHEN 72 THEN 6 WHEN 11 THEN 7 WHEN 192 THEN 8 ELSE 9 END, pais_id').fetchall()
        except sqlite3.Error:
            rows = self.connection.execute('SELECT DISTINCT pais_id AS pais_id,NULL AS nome,NULL AS codigo FROM times WHERE pais_id IS NOT NULL ORDER BY pais_id').fetchall()
        items = []
        for row in rows:
            name, code = self._country_details(int(row[0]))
            if search and search not in name.lower() and search not in str(code or '').lower():
                continue
            try:
                club_count = int(self.connection.execute('SELECT COUNT(*) FROM times WHERE pais_id=?', (int(row[0]),)).fetchone()[0])
            except sqlite3.Error:
                club_count = 0
            if club_count:
                known_names = {29, 104, 65, 154, 97, 3, 72, 11, 192}
                if name.startswith('País ID') and int(row[0]) not in known_names:
                    continue
                source = self._first_division_source(int(row[0]))
                first_division_count = 0
                if source is not None:
                    try:
                        report = resolve_first_division_members(self.connection, int(row[0]))
                        if not report['unmatched'] and not report['ambiguous']:
                            first_division_count = len(report['matched'])
                    except (sqlite3.Error, ValueError):
                        first_division_count = 0
                items.append({'countryId': int(row[0]), 'name': name, 'code': code, 'clubCount': club_count, 'firstDivisionClubCount': first_division_count, 'firstDivisionName': source.competition_name if source else None, 'supported': bool(source and first_division_count > 0)})
            if len(items) >= limit:
                break
        return items

    def _first_division_source(self, country_id: int):
        return next((source for source in FIRST_DIVISION_SOURCES if source.country_id == int(country_id)), None)

    def _import_first_division_membership(self, country_id: int) -> dict[str, Any]:
        report = resolve_first_division_members(self.connection, int(country_id))
        if report['unmatched'] or report['ambiguous']:
            raise ValueError('FIRST_DIVISION_MEMBERSHIP_INVALID')
        source = self._first_division_source(int(country_id))
        assert source is not None
        imported_at = self._now()
        for item in report['matched']:
            self.connection.execute('INSERT OR REPLACE INTO first_division_membership(country_id,club_id,source_name,source_url,season_label,imported_at) VALUES(?,?,?,?,?,?)', (source.country_id, item['teamId'], item['sourceName'], source.source_url, source.season_label, imported_at))
        return report

    def list_first_division_clubs(self, country_ids: list[int]) -> list[dict[str, Any]]:
        clubs = []
        seen: set[int] = set()
        for country_id in country_ids:
            report = resolve_first_division_members(self.connection, int(country_id))
            if report['unmatched'] or report['ambiguous']:
                raise ValueError('FIRST_DIVISION_MEMBERSHIP_INVALID')
            for item in report['matched']:
                if item['teamId'] not in seen:
                    clubs.append(item)
                    seen.add(item['teamId'])
        return clubs

    @staticmethod
    def _round_robin_pairs(team_ids: list[int]):
        teams = list(team_ids)
        if len(teams) % 2:
            teams.append(None)
        for round_number in range(len(teams) - 1):
            half = len(teams) // 2
            for index in range(half):
                left, right = teams[index], teams[-1 - index]
                if left is None or right is None:
                    continue
                home, away = (left, right) if (round_number + index) % 2 == 0 else (right, left)
                yield round_number + 1, home, away
            teams = [teams[0], teams[-1], *teams[1:-1]]

    def _seed_parallel_season(self, career_id: int, season_number: int = 1) -> int:
        now = self._now()
        entries = self.connection.execute('SELECT club_id,parallel_division,parallel_position FROM career_parallel_entries WHERE career_id=? AND status=? ORDER BY parallel_division,parallel_position', (career_id, 'ACTIVE')).fetchall()
        self.connection.execute('DELETE FROM career_parallel_standings WHERE career_id=? AND season_number=?', (career_id, season_number))
        self.connection.execute('DELETE FROM career_parallel_fixtures WHERE career_id=? AND season_number=?', (career_id, season_number))
        by_division: dict[int, list[int]] = {}
        for entry in entries:
            by_division.setdefault(int(entry['parallel_division']), []).append(int(entry['club_id']))
            self.connection.execute('INSERT INTO career_parallel_standings(career_id,season_number,club_id,division,position,updated_at) VALUES(?,?,?,?,?,?)', (career_id, season_number, entry['club_id'], entry['parallel_division'], entry['parallel_position'], now))
        fixture_count = 0
        season_start = date(2026 + season_number - 1, 8, 1)
        for division, clubs in by_division.items():
            first_leg = list(self._round_robin_pairs(clubs))
            round_count = max((item[0] for item in first_leg), default=0)
            for matchday, home, away in first_leg:
                scheduled = season_start + __import__('datetime').timedelta(weeks=matchday - 1)
                self.connection.execute('INSERT INTO career_parallel_fixtures(career_id,season_number,matchday,leg,division,scheduled_date,home_club_id,away_club_id) VALUES(?,?,?,?,?,?,?,?)', (career_id, season_number, matchday, 1, division, scheduled.isoformat(), home, away))
                fixture_count += 1
                scheduled_second = season_start + __import__('datetime').timedelta(weeks=round_count + matchday - 1)
                self.connection.execute('INSERT INTO career_parallel_fixtures(career_id,season_number,matchday,leg,division,scheduled_date,home_club_id,away_club_id) VALUES(?,?,?,?,?,?,?,?)', (career_id, season_number, round_count + matchday, 2, division, scheduled_second.isoformat(), away, home))
                fixture_count += 1
        return fixture_count

    def record_parallel_result(self, career_id: int, fixture_id: int, home_goals: int, away_goals: int) -> dict[str, Any]:
        home_goals, away_goals = int(home_goals), int(away_goals)
        if home_goals < 0 or away_goals < 0:
            raise ValueError('PARALLEL_RESULT_INVALID')
        with self.connection:
            fixture = self.connection.execute('SELECT * FROM career_parallel_fixtures WHERE career_id=? AND fixture_id=?', (career_id, fixture_id)).fetchone()
            if not fixture:
                raise ValueError('PARALLEL_FIXTURE_NOT_FOUND')
            if fixture['status'] == 'PLAYED':
                return {'fixture_id': fixture_id, 'status': 'ALREADY_PLAYED', 'home_goals': fixture['home_goals'], 'away_goals': fixture['away_goals']}
            self.connection.execute("UPDATE career_parallel_fixtures SET status='PLAYED',home_goals=?,away_goals=?,played_at=? WHERE fixture_id=?", (home_goals, away_goals, self._now(), fixture_id))
            for club_id, goals_for, goals_against, won, drawn, lost, points in (
                (fixture['home_club_id'], home_goals, away_goals, int(home_goals > away_goals), int(home_goals == away_goals), int(home_goals < away_goals), 3 if home_goals > away_goals else 1 if home_goals == away_goals else 0),
                (fixture['away_club_id'], away_goals, home_goals, int(away_goals > home_goals), int(away_goals == home_goals), int(away_goals < home_goals), 3 if away_goals > home_goals else 1 if home_goals == away_goals else 0),
            ):
                self.connection.execute('UPDATE career_parallel_standings SET played=played+1,wins=wins+?,draws=draws+?,losses=losses+?,goals_for=goals_for+?,goals_against=goals_against+?,points=points+?,updated_at=? WHERE career_id=? AND season_number=? AND club_id=?', (won, drawn, lost, goals_for, goals_against, points, self._now(), career_id, fixture['season_number'], club_id))
            return {'fixture_id': fixture_id, 'status': 'PLAYED', 'home_goals': home_goals, 'away_goals': away_goals}

    def close_parallel_season(self, career_id: int, season_number: int = 1) -> dict[str, Any]:
        existing = self.connection.execute('SELECT * FROM career_parallel_season_closures WHERE career_id=? AND season_number=?', (career_id, season_number)).fetchone()
        if existing:
            return {'status': 'ALREADY_CLOSED', 'career_id': career_id, 'season_number': season_number, 'promoted_count': existing['promoted_count'], 'relegated_count': existing['relegated_count']}
        rows = self.connection.execute('SELECT * FROM career_parallel_standings WHERE career_id=? AND season_number=? ORDER BY division,points DESC,(goals_for-goals_against) DESC,goals_for DESC,club_id', (career_id, season_number)).fetchall()
        if not rows:
            raise ValueError('PARALLEL_SEASON_NOT_FOUND')
        grouped: dict[int, list[Any]] = {}
        for row in rows:
            grouped.setdefault(int(row['division']), []).append(row)
        moves: dict[int, int] = {}
        for division in range(1, 5):
            table = grouped.get(division, [])
            if division > 1 and table:
                for row in table[:2]: moves[int(row['club_id'])] = division - 1
            if division < 4 and table:
                for row in table[-2:]: moves[int(row['club_id'])] = division + 1
        with self.connection:
            for club_id, division in moves.items():
                self.connection.execute('UPDATE career_parallel_entries SET parallel_division=?,parallel_position=0,status=? WHERE career_id=? AND club_id=?', (division, 'ACTIVE', career_id, club_id))
            positions: dict[int, int] = {}
            for row in self.connection.execute('SELECT club_id,parallel_division FROM career_parallel_entries WHERE career_id=? ORDER BY parallel_division,club_id', (career_id,)).fetchall():
                division = int(row['parallel_division']); positions[division] = positions.get(division, 0) + 1
                self.connection.execute('UPDATE career_parallel_entries SET parallel_position=? WHERE career_id=? AND club_id=?', (positions[division], career_id, row['club_id']))
            details = {'moves': [{'club_id': club_id, 'division': division} for club_id, division in sorted(moves.items())]}
            self.connection.execute('INSERT INTO career_parallel_season_closures(career_id,season_number,closed_at,promoted_count,relegated_count,details) VALUES(?,?,?,?,?,?)', (career_id, season_number, self._now(), sum(1 for row in moves.values() if row < 4), sum(1 for row in moves.values() if row > 1), json.dumps(details, sort_keys=True)))
            next_fixtures = self._seed_parallel_season(career_id, season_number + 1)
        return {'status': 'CLOSED', 'career_id': career_id, 'season_number': season_number, 'promoted_count': sum(1 for row in moves.values() if row < 4), 'relegated_count': sum(1 for row in moves.values() if row > 1), 'next_season': season_number + 1, 'next_fixtures': next_fixtures, 'moves': details['moves']}

    def parallel_league_snapshot(self, career_id: int, season_number: int = 1) -> dict[str, Any]:
        league = self.connection.execute('SELECT * FROM career_parallel_leagues WHERE career_id=?', (career_id,)).fetchone()
        if not league:
            raise ValueError('PARALLEL_LEAGUE_NOT_FOUND')
        standings = [dict(row) for row in self.connection.execute('SELECT s.*,t.nome AS club_name FROM career_parallel_standings s LEFT JOIN times t ON t.time_id=s.club_id WHERE s.career_id=? AND s.season_number=? ORDER BY s.division,s.position', (career_id, season_number)).fetchall()]
        fixtures = [dict(row) for row in self.connection.execute('SELECT * FROM career_parallel_fixtures WHERE career_id=? AND season_number=? ORDER BY matchday,division,fixture_id LIMIT 500', (career_id, season_number)).fetchall()]
        return {'league': dict(league), 'season_number': season_number, 'standings': standings, 'fixtures': fixtures, 'fixture_count': int(self.connection.execute('SELECT COUNT(*) FROM career_parallel_fixtures WHERE career_id=? AND season_number=?', (career_id, season_number)).fetchone()[0]), 'played_count': int(self.connection.execute("SELECT COUNT(*) FROM career_parallel_fixtures WHERE career_id=? AND season_number=? AND status='PLAYED'", (career_id, season_number)).fetchone()[0])}

    def preview_parallel_league(self, country_ids: list[int], target_type: str, target_id: int) -> dict[str, Any]:
        countries = list(dict.fromkeys(int(country_id) for country_id in country_ids))
        clubs = [{'club_id': item['teamId'], 'origin_country_id': item['countryId'], 'name': item.get('teamName')} for item in self.list_first_division_clubs(countries)]
        target_in_first_division = target_type == 'club' and target_id in {item['club_id'] for item in clubs}
        if len(countries) > 1 and target_type == 'club' and not target_in_first_division:
            raise ValueError('TARGET_CLUB_NOT_FIRST_DIVISION')
        if len(countries) == 1:
            return {'mode': 'NATIONAL', 'competition_name': self._first_division_source(countries[0]).competition_name if self._first_division_source(countries[0]) else self._country_details(countries[0])[0], 'total_clubs': len(clubs), 'country_count': 1, 'division_count': 4, 'seed': None, 'target_division': 4 if target_in_first_division else None, 'divisions': [], 'read_only': True, 'preserved_national_competition': True}
        seed = hashlib.sha256(f'preview:{"/".join(str(value) for value in countries)}'.encode()).hexdigest()[:16]
        import random
        randomizer = random.Random(int(seed, 16)); randomizer.shuffle(clubs)
        if target_type == 'club':
            target_index = next(index for index, item in enumerate(clubs) if item['club_id'] == target_id)
            clubs[target_index], clubs[-max(1, len(clubs) // 4)] = clubs[-max(1, len(clubs) // 4)], clubs[target_index]
        base, remainder = divmod(len(clubs), 4)
        capacities = [base + (1 if division <= remainder else 0) for division in range(1, 5)]
        divisions = []; cursor = 0
        for division, capacity in enumerate(capacities, start=1):
            divisions.append({'division': division, 'clubs': clubs[cursor:cursor + capacity]})
            cursor += capacity
        return {'mode': 'PARALLEL', 'competition_name': f'Liga Mundial · {len(countries)} países', 'total_clubs': len(clubs), 'country_count': len(countries), 'division_count': 4, 'seed': seed, 'target_division': 4 if target_type == 'club' else None, 'divisions': divisions, 'read_only': True, 'preserved_national_competition': True}

    def _materialize_parallel_league(self, career_id: int, manager_id: int, career_name: str, season_id: int | None, country_ids: list[int], target_type: str, target_id: int) -> dict[str, Any]:
        if len(country_ids) == 1:
            report = self._import_first_division_membership(country_ids[0])
            matched_ids = {item['teamId'] for item in report['matched']}
            target_division = None
            if target_type == 'club' and target_id in matched_ids:
                self.connection.execute('INSERT INTO career_national_reassignments(career_id,manager_id,club_id,country_id,original_division,career_division,status,created_at) VALUES(?,?,?,?,?,?,?,?)', (career_id, manager_id, target_id, country_ids[0], 1, 4, 'ACTIVE', self._now()))
                target_division = 4
            return {'mode': 'NATIONAL', 'name': report['competitionName'], 'total_clubs': report['expected'], 'country_count': 1, 'division_count': 4, 'seed': None, 'target_division': target_division, 'fixture_count': 0, 'season_number': 1, 'preserved_national_competition': True}
        reports = [self._import_first_division_membership(country_id) for country_id in country_ids]
        clubs = []
        seen: set[int] = set()
        for report in reports:
            for item in report['matched']:
                if item['teamId'] in seen:
                    raise ValueError('FIRST_DIVISION_CLUB_DUPLICATED')
                seen.add(item['teamId'])
                clubs.append({'club_id': item['teamId'], 'origin_country_id': report['countryId']})
        if not clubs:
            raise ValueError('PARALLEL_LEAGUE_EMPTY')
        if target_type == 'club' and target_id not in seen:
            raise ValueError('TARGET_CLUB_NOT_FIRST_DIVISION')
        seed = hashlib.sha256(f'{career_id}:{"/".join(str(value) for value in country_ids)}'.encode()).hexdigest()[:16]
        import random
        randomizer = random.Random(int(seed, 16))
        randomizer.shuffle(clubs)
        if target_type == 'club':
            target_index = next(index for index, item in enumerate(clubs) if item['club_id'] == target_id)
            d4_start = len(clubs) - max(1, len(clubs) // 4)
            clubs[target_index], clubs[d4_start] = clubs[d4_start], clubs[target_index]
        base, remainder = divmod(len(clubs), 4)
        capacities = [base + (1 if division <= remainder else 0) for division in range(1, 5)]
        self.connection.execute('INSERT INTO career_parallel_leagues(career_id,manager_id,name,season_id,total_clubs,source_country_count,seed,division_count,created_at) VALUES(?,?,?,?,?,?,?,?,?)', (career_id, manager_id, f'{career_name} · Liga Mundial', season_id, len(clubs), len(country_ids), seed, 4, self._now()))
        cursor = 0
        for division, capacity in enumerate(capacities, start=1):
            for position, item in enumerate(clubs[cursor:cursor + capacity], start=1):
                self.connection.execute('INSERT INTO career_parallel_entries(career_id,club_id,origin_country_id,origin_division,parallel_division,parallel_position) VALUES(?,?,?,?,?,?)', (career_id, item['club_id'], item['origin_country_id'], 1, division, position))
            cursor += capacity
        fixture_count = self._seed_parallel_season(career_id, 1)
        return {'name': f'{career_name} · Liga Mundial', 'total_clubs': len(clubs), 'country_count': len(country_ids), 'division_count': 4, 'seed': seed, 'target_division': 4 if target_type == 'club' else None, 'fixture_count': fixture_count, 'season_number': 1}

    def create_career(self, manager_id: int, name: str = 'Carreira', club_id: int | None = None, season_id: int | None = None):
        if self.connection.execute("SELECT 1 FROM manager_careers WHERE manager_id=? AND status='ACTIVE'", (manager_id,)).fetchone():
            raise ValueError('ACTIVE_CAREER_EXISTS')
        now = self._now()
        cur = self.connection.execute('INSERT INTO manager_careers(manager_id,name,created_at,updated_at,season_id,current_club_id,engine_version) VALUES(?,?,?,?,?,?,?)', (manager_id, name, now, now, season_id, club_id, self.ENGINE_VERSION))
        career_id = int(cur.lastrowid)
        self.connection.execute('UPDATE managers SET current_club_id=?,active_career=1,status=? WHERE manager_id=?', (club_id, ManagerStatus.ACTIVE, manager_id))
        self.connection.commit()
        return career_id

    def start_career(self, manager_name: str, nationality: str | None, age: int, career_name: str = 'Carreira', target_type: str = 'club', target_id: int | None = None, season_id: int | None = None, selected_country_ids: list[int] | None = None) -> dict[str, Any]:
        manager_name = (manager_name or '').strip()
        career_name = (career_name or 'Carreira').strip() or 'Carreira'
        age = int(age)
        if not manager_name: raise ValueError('MANAGER_NAME_REQUIRED')
        if age < 18: raise ValueError('MANAGER_AGE_INVALID')
        if target_type not in ('club', 'selection'): raise ValueError('CAREER_TARGET_INVALID')
        if target_id is None: raise ValueError('CAREER_TARGET_REQUIRED')
        target_id = int(target_id)
        if target_type == 'club' and not self.connection.execute('SELECT 1 FROM times WHERE time_id=?', (target_id,)).fetchone(): raise ValueError('CLUB_NOT_FOUND')
        if target_type == 'selection' and not self.connection.execute('SELECT 1 FROM selecoes WHERE selecao_id=?', (target_id,)).fetchone(): raise ValueError('SELECTION_NOT_FOUND')
        target_country_id = None
        if target_type == 'club':
            target_country_id = self.connection.execute('SELECT pais_id FROM times WHERE time_id=?', (target_id,)).fetchone()[0]
        countries = []
        for country_id in selected_country_ids or ([] if target_country_id is None else [target_country_id]):
            country_id = int(country_id)
            if country_id not in countries:
                countries.append(country_id)
        if not countries:
            raise ValueError('WORLD_COUNTRIES_REQUIRED')
        for country_id in countries:
            try:
                exists = self.connection.execute('SELECT 1 FROM paises WHERE pais_id=?', (country_id,)).fetchone()
            except sqlite3.Error:
                exists = self.connection.execute('SELECT 1 FROM times WHERE pais_id=?', (country_id,)).fetchone()
            if not exists:
                raise ValueError('WORLD_COUNTRY_NOT_FOUND')
        if target_country_id is not None and target_country_id not in countries:
            raise ValueError('TARGET_COUNTRY_NOT_SELECTED')
        country_names = [self._country_details(country_id)[0] for country_id in countries]
        today = date.today().isoformat(); club_id = target_id if target_type == 'club' else None
        with self.connection:
            self.connection.execute("UPDATE manager_careers SET status='PAUSED', updated_at=? WHERE status='ACTIVE'", (today,))
            mid = int(self.connection.execute('INSERT INTO managers(name,nationality,age,created_at,current_club_id,active_career) VALUES(?,?,?,?,?,1)', (manager_name, nationality or None, age, today, club_id)).lastrowid)
            cid = int(self.connection.execute('INSERT INTO manager_careers(manager_id,name,created_at,updated_at,season_id,current_club_id,engine_version,starting_division) VALUES(?,?,?,?,?,?,?,?)', (mid, career_name, today, today, season_id, club_id, self.ENGINE_VERSION, 4)).lastrowid)
            parallel_league = self._materialize_parallel_league(cid, mid, career_name, season_id, countries, target_type, target_id)
            world_mode = 'NATIONAL' if len(countries) == 1 else 'PARALLEL'
            self.connection.execute('INSERT INTO career_world_configs(career_id,manager_id,combined_name,starting_division,world_mode,created_at) VALUES(?,?,?,?,?,?)', (cid, mid, ' + '.join(country_names), 4, world_mode, today))
            for country_id, country_name in zip(countries, country_names):
                self.connection.execute('INSERT INTO career_world_countries(career_id,country_id,country_name,country_code) VALUES(?,?,?,?)', (cid, country_id, country_name, self._country_details(country_id)[1]))
            if target_type == 'selection': self.connection.execute('INSERT INTO manager_selection_assignments(manager_id,career_id,selection_id,status,appointed_at) VALUES(?,?,?,?,?)', (mid, cid, target_id, 'ACTIVE', today))
            self.connection.execute('INSERT INTO manager_history(manager_id,club_id,event_type,event_date,payload) VALUES(?,?,?,?,?)', (mid, club_id, 'CAREER_STARTED', today, f'{target_type}:{target_id}'))
        return {'manager_id': mid, 'career_id': cid, 'target_type': target_type, 'target_id': target_id, 'current_club_id': club_id, 'engine_version': self.ENGINE_VERSION, 'selected_country_ids': countries, 'combined_league_name': ' + '.join(country_names), 'starting_division': parallel_league.get('target_division') if parallel_league.get('mode') == 'NATIONAL' else 4, 'world_mode': parallel_league.get('mode'), 'parallel_league': parallel_league}

    def set_preference(self, manager_id: int, key: str, value: Any) -> None:
        if not key.strip(): raise ValueError('PREFERENCE_KEY_REQUIRED')
        self.connection.execute('INSERT INTO manager_preferences(manager_id,preference_key,preference_value,updated_at) VALUES(?,?,?,?) ON CONFLICT(manager_id,preference_key) DO UPDATE SET preference_value=excluded.preference_value,updated_at=excluded.updated_at', (manager_id, key, json.dumps(value, ensure_ascii=False), self._now()))
        self.connection.commit()

    def get_preferences(self, manager_id: int) -> dict[str, Any]:
        rows = self.connection.execute('SELECT preference_key,preference_value FROM manager_preferences WHERE manager_id=?', (manager_id,)).fetchall()
        return {row['preference_key']: json.loads(row['preference_value']) for row in rows}

    def snapshot_hash(self, snapshot_id: int) -> str:
        row=self.connection.execute('SELECT payload FROM career_snapshots WHERE snapshot_id=?',(snapshot_id,)).fetchone()
        if not row: raise ValueError('SNAPSHOT_NOT_FOUND')
        return hashlib.sha256(str(row['payload']).encode()).hexdigest()

    def compare_snapshots(self, left_id: int, right_id: int) -> dict:
        left=self.connection.execute('SELECT career_id,payload FROM career_snapshots WHERE snapshot_id=?',(left_id,)).fetchone(); right=self.connection.execute('SELECT career_id,payload FROM career_snapshots WHERE snapshot_id=?',(right_id,)).fetchone()
        if not left or not right: raise ValueError('SNAPSHOT_NOT_FOUND')
        return {'left_id':int(left_id),'right_id':int(right_id),'same_career':int(left['career_id'])==int(right['career_id']),'left_hash':hashlib.sha256(str(left['payload']).encode()).hexdigest(),'right_hash':hashlib.sha256(str(right['payload']).encode()).hexdigest(),'identical':str(left['payload'])==str(right['payload']),'read_only':True}

    def retain_snapshots(self, career_id: int, keep: int = 10) -> int:
        if int(keep)<1: raise ValueError('SNAPSHOT_RETENTION_INVALID')
        rows=self.connection.execute('SELECT snapshot_id FROM career_snapshots WHERE career_id=? ORDER BY snapshot_id DESC',(career_id,)).fetchall(); removed=rows[int(keep):]
        with self.connection:
            for row in removed: self.connection.execute('DELETE FROM career_snapshots WHERE snapshot_id=?',(row['snapshot_id'],))
        return len(removed)

    def restore_selective(self, manager_id: int, snapshot_id: int, fields: list[str]) -> dict:
        allowed={'current_club_id','season_id','status','name'}
        if not fields or not set(fields)<=allowed: raise ValueError('SNAPSHOT_FIELDS_INVALID')
        row=self.connection.execute('SELECT * FROM career_snapshots WHERE snapshot_id=? AND manager_id=?',(snapshot_id,manager_id)).fetchone()
        if not row: raise ValueError('SNAPSHOT_NOT_FOUND')
        payload=json.loads(row['payload']); career=payload['career']; career_id=int(career['career_id'])
        assignments=[]; values=[]
        for field in fields: assignments.append(field+'=?'); values.append(career.get(field))
        values.append(career_id)
        with self.connection:
            self.connection.execute('UPDATE manager_careers SET '+','.join(assignments)+' WHERE career_id=?',values)
            if 'current_club_id' in fields: self.connection.execute('UPDATE managers SET current_club_id=? WHERE manager_id=?',(career.get('current_club_id'),manager_id))
            self.connection.execute('INSERT INTO career_snapshot_audit(snapshot_id,career_id,action,success,details,created_at) VALUES(?,?,?,?,?,?)',(snapshot_id,career_id,'RESTORE_SELECTIVE',1,json.dumps({'fields':fields},sort_keys=True),self._now()))
        return {'snapshot_id':int(snapshot_id),'career_id':career_id,'fields':fields,'restored':True,'hash':self.snapshot_hash(snapshot_id)}

    def recovery_audit(self, career_id: int) -> list[dict]:
        return [dict(row) for row in self.connection.execute('SELECT * FROM career_snapshot_audit WHERE career_id=? ORDER BY audit_id',(career_id,)).fetchall()]

    def snapshot(self, career_id: int) -> int:
        row = self.connection.execute('SELECT manager_id FROM manager_careers WHERE career_id=?', (career_id,)).fetchone()
        if not row: raise ValueError('CAREER_NOT_FOUND')
        manager = self.connection.execute('SELECT * FROM managers WHERE manager_id=?', (row['manager_id'],)).fetchone()
        career = self.connection.execute('SELECT * FROM manager_careers WHERE career_id=?', (career_id,)).fetchone()
        payload = json.dumps({'manager': dict(manager), 'career': dict(career)}, ensure_ascii=False, sort_keys=True)
        cur = self.connection.execute('INSERT INTO career_snapshots(career_id,manager_id,created_at,engine_version,payload) VALUES(?,?,?,?,?)', (career_id, row['manager_id'], self._now(), self.ENGINE_VERSION, payload))
        self.connection.commit()
        return int(cur.lastrowid)

    def switch_club(self, manager_id: int, destination_club_id: int, reference: str) -> None:
        with self.connection:
            row = self.connection.execute("SELECT career_id,current_club_id FROM manager_careers WHERE manager_id=? AND status='ACTIVE'", (manager_id,)).fetchone()
            if not row: self._audit_permission(manager_id, 'switch_club', False, 'NO_ACTIVE_CAREER'); raise ValueError('NO_ACTIVE_CAREER')
            if not self.connection.execute('SELECT 1 FROM times WHERE time_id=?', (destination_club_id,)).fetchone(): self._audit_permission(manager_id, 'switch_club', False, 'CLUB_NOT_FOUND'); raise ValueError('CLUB_NOT_FOUND')
            if self.connection.execute('SELECT 1 FROM career_change_audit WHERE reference=?', (reference,)).fetchone(): return
            self.connection.execute('UPDATE manager_careers SET current_club_id=?,updated_at=? WHERE career_id=?', (destination_club_id, self._now(), row['career_id']))
            self.connection.execute('UPDATE managers SET current_club_id=? WHERE manager_id=?', (destination_club_id, manager_id))
            self.connection.execute('INSERT INTO career_change_audit(career_id,manager_id,origin_club_id,destination_club_id,created_at,reference) VALUES(?,?,?,?,?,?)', (row['career_id'], manager_id, row['current_club_id'], destination_club_id, self._now(), reference))
            self.connection.execute('INSERT INTO manager_history(manager_id,club_id,event_type,event_date,payload) VALUES(?,?,?,?,?)', (manager_id, destination_club_id, 'CLUB_CHANGED', date.today().isoformat(), reference))
            self._audit_permission(manager_id, 'switch_club', True, 'ALLOWED')

    def close_career(self, manager_id: int, reason: str = 'manager decision') -> int:
        with self.connection:
            row = self.connection.execute("SELECT career_id,current_club_id FROM manager_careers WHERE manager_id=? AND status='ACTIVE'", (manager_id,)).fetchone()
            if not row: raise ValueError('NO_ACTIVE_CAREER')
            snapshot_id = self.snapshot(row['career_id'])
            self.connection.execute("UPDATE manager_careers SET status='CLOSED',updated_at=? WHERE career_id=?", (self._now(), row['career_id']))
            self.connection.execute("UPDATE managers SET status='RESIGNED',active_career=0 WHERE manager_id=?", (manager_id,))
            self.connection.execute('INSERT INTO manager_history(manager_id,club_id,event_type,event_date,payload) VALUES(?,?,?,?,?)', (manager_id, row['current_club_id'], 'CAREER_CLOSED', date.today().isoformat(), json.dumps({'reason': reason, 'snapshot_id': snapshot_id})))
            return snapshot_id

    def resume_career(self, manager_id: int, snapshot_id: int) -> dict[str, Any]:
        row = self.connection.execute('SELECT * FROM career_snapshots WHERE snapshot_id=? AND manager_id=?', (snapshot_id, manager_id)).fetchone()
        if not row: raise ValueError('SNAPSHOT_NOT_FOUND')
        payload = json.loads(row['payload']); career_id = int(payload['career']['career_id'])
        with self.connection:
            self.connection.execute("UPDATE manager_careers SET status='ACTIVE',updated_at=? WHERE career_id=?", (self._now(), career_id))
            self.connection.execute("UPDATE managers SET status='ACTIVE',active_career=1,current_club_id=? WHERE manager_id=?", (payload['career']['current_club_id'], manager_id))
        return {'manager_id': manager_id, 'career_id': career_id, 'current_club_id': payload['career']['current_club_id'], 'snapshot_id': snapshot_id}

    def sign(self, manager_id: int, club_id: int, start: str, end: str, salary: int, objective: str | None = None, bonus: int = 0) -> None:
        c = self.connection.execute("SELECT career_id FROM manager_careers WHERE manager_id=? AND status='ACTIVE'", (manager_id,)).fetchone()
        if not c: raise ValueError('NO_ACTIVE_CAREER')
        self.connection.execute("UPDATE manager_contracts SET status='TERMINATED',end_date=? WHERE manager_id=? AND status='ACTIVE'", (start, manager_id))
        self.connection.execute('INSERT INTO manager_contracts(manager_id,club_id,start_date,end_date,salary,bonus,objective) VALUES(?,?,?,?,?,?,?)', (manager_id, club_id, start, end, salary, bonus, objective))
        self.connection.execute('UPDATE managers SET current_club_id=? WHERE manager_id=?', (club_id, manager_id)); self.connection.execute('UPDATE manager_careers SET current_club_id=?,updated_at=? WHERE career_id=?', (club_id, self._now(), c['career_id']))
        self.connection.execute('INSERT INTO manager_history(manager_id,club_id,event_type,event_date,payload) VALUES(?,?,?,?,?)', (manager_id, club_id, 'CLUB_SIGNED', date.today().isoformat(), objective or '')); self.connection.commit()

    def objective(self, career_id: int, type_: str, priority: int = 50, deadline: str | None = None) -> int:
        cur = self.connection.execute('INSERT INTO manager_objectives(career_id,type,priority,deadline) VALUES(?,?,?,?)', (career_id, type_, priority, deadline)); self.connection.commit(); return int(cur.lastrowid)

    def inbox(self, manager_id: int, type_: str, title: str, body: str = '', reference: str | None = None) -> None:
        self.connection.execute('INSERT OR IGNORE INTO manager_inbox(manager_id,type,title,body,reference,created_at) VALUES(?,?,?,?,?,?)', (manager_id, type_, title, body, reference, date.today().isoformat())); self.connection.commit()

    def resign(self, manager_id: int, reason: str = 'manager decision') -> None:
        with self.connection:
            r = self.connection.execute('SELECT current_club_id FROM managers WHERE manager_id=?', (manager_id,)).fetchone(); self.connection.execute("UPDATE managers SET status='RESIGNED',active_career=0 WHERE manager_id=?", (manager_id,)); self.connection.execute("UPDATE manager_contracts SET status='RESIGNED' WHERE manager_id=? AND status='ACTIVE'", (manager_id,)); self.connection.execute('INSERT INTO manager_history(manager_id,club_id,event_type,event_date,payload) VALUES(?,?,?,?,?)', (manager_id, r['current_club_id'] if r else None, 'RESIGNED', date.today().isoformat(), reason))

    def load(self, manager_id: int): return self.connection.execute('SELECT * FROM managers WHERE manager_id=?', (manager_id,)).fetchone()
    def close(self): self.connection.close()
