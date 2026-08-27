from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from engine.core.state_store import assert_mutable_state_path
from engine.economy.staff_market import DEPARTMENTS

SCHEMA = """
CREATE TABLE IF NOT EXISTS training_plans(
 plan_id INTEGER PRIMARY KEY AUTOINCREMENT, club_id INTEGER NOT NULL, season INTEGER NOT NULL, week INTEGER NOT NULL,
 plan_type TEXT NOT NULL, load INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'PLANNED', created_at TEXT NOT NULL,
 UNIQUE(club_id,season,week)
);
CREATE TABLE IF NOT EXISTS training_sessions(
 session_id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id INTEGER NOT NULL, player_id INTEGER NOT NULL,
 load INTEGER NOT NULL, recovery_days INTEGER NOT NULL DEFAULT 0, injury_risk REAL NOT NULL DEFAULT 0,
 status TEXT NOT NULL DEFAULT 'PLANNED', FOREIGN KEY(plan_id) REFERENCES training_plans(plan_id)
);
CREATE TABLE IF NOT EXISTS training_history(
 history_id INTEGER PRIMARY KEY AUTOINCREMENT, club_id INTEGER NOT NULL, event_type TEXT NOT NULL,
 event_date TEXT NOT NULL, payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_training_sessions_plan ON training_sessions(plan_id);
CREATE INDEX IF NOT EXISTS idx_training_history_club ON training_history(club_id,event_date);
CREATE TABLE IF NOT EXISTS individual_training_plans(
 individual_plan_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,player_id INTEGER NOT NULL,season INTEGER NOT NULL,focus TEXT NOT NULL,weekly_load INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'DRAFT',created_at TEXT NOT NULL,UNIQUE(club_id,player_id,season,focus)
);
CREATE TABLE IF NOT EXISTS individual_training_sessions(
 session_id INTEGER PRIMARY KEY AUTOINCREMENT,individual_plan_id INTEGER NOT NULL,session_date TEXT NOT NULL,load INTEGER NOT NULL,compatibility REAL NOT NULL,risk REAL NOT NULL,status TEXT NOT NULL DEFAULT 'PLANNED',FOREIGN KEY(individual_plan_id) REFERENCES individual_training_plans(individual_plan_id)
);
CREATE TABLE IF NOT EXISTS training_evolution_history(
 evolution_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,player_id INTEGER NOT NULL,season INTEGER NOT NULL,source TEXT NOT NULL,delta REAL NOT NULL,created_at TEXT NOT NULL,reference TEXT UNIQUE
);
CREATE TABLE IF NOT EXISTS training_plan_versions(
 version_id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id INTEGER NOT NULL, version INTEGER NOT NULL,
 author TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'DRAFT', created_at TEXT NOT NULL,
 UNIQUE(plan_id,version), FOREIGN KEY(plan_id) REFERENCES training_plans(plan_id)
);
CREATE TABLE IF NOT EXISTS training_microcycles(microcycle_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,season INTEGER NOT NULL,week INTEGER NOT NULL,focus TEXT NOT NULL,intensity INTEGER NOT NULL,rest_days INTEGER NOT NULL DEFAULT 1,status TEXT NOT NULL DEFAULT 'DRAFT',UNIQUE(club_id,season,week));
CREATE TABLE IF NOT EXISTS training_audit(audit_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,plan_id INTEGER,action TEXT NOT NULL,payload TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS training_objectives(
 objective_id INTEGER PRIMARY KEY AUTOINCREMENT, club_id INTEGER NOT NULL, player_id INTEGER NOT NULL,
 season INTEGER NOT NULL, metric TEXT NOT NULL, target REAL NOT NULL, current_value REAL NOT NULL DEFAULT 0,
 status TEXT NOT NULL DEFAULT 'ACTIVE', created_at TEXT NOT NULL,
 UNIQUE(club_id,player_id,season,metric)
);
"""

PLAN_TYPES = frozenset({"GENERAL", "TECHNICAL", "TACTICAL", "PHYSICAL", "SET_PIECES", "REST"})


class TrainingService:
    def __init__(self, database: str | Path | sqlite3.Connection):
        if isinstance(database, sqlite3.Connection):
            self.connection = database
        else:
            assert_mutable_state_path(database)
            self.connection = sqlite3.connect(str(database))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def close(self):
        self.connection.close()

    def _assert_club(self, club_id: int):
        if self.connection.execute("SELECT 1 FROM times WHERE time_id=?", (int(club_id),)).fetchone() is None:
            raise ValueError("CLUB_NOT_FOUND")

    def department_inventory(self, club_id: int) -> list[dict]:
        self._assert_club(club_id)
        rows = self.connection.execute("SELECT department,level,cost,capacity,maintenance,efficiency FROM club_departments WHERE club_id=? ORDER BY department", (int(club_id),)).fetchall()
        by_name = {str(row["department"]): dict(row) for row in rows}
        result = []
        for name, rule in DEPARTMENTS.items():
            current = by_name.get(name)
            level = int(current["level"]) if current else 0
            result.append({"department": name, "label": rule["label"], "level": level, "max_level": 10, "purchase_base": int(rule["purchase"]), "maintenance": int(current["maintenance"]) if current else 0, "capacity": int(current["capacity"]) if current else 0, "efficiency": float(current["efficiency"]) if current else 0.0})
        return result

    def create_microcycle(self, club_id: int, season: int, week: int, focus: str, intensity: int = 50, rest_days: int = 1) -> dict:
        self._assert_club(club_id)
        if not str(focus).strip() or not 0<=int(intensity)<=100 or not 0<=int(rest_days)<=7: raise ValueError('MICROCYCLE_INVALID')
        with self.connection: self.connection.execute('INSERT OR REPLACE INTO training_microcycles(club_id,season,week,focus,intensity,rest_days) VALUES(?,?,?,?,?,?)',(club_id,season,week,focus,intensity,rest_days))
        return dict(self.connection.execute('SELECT * FROM training_microcycles WHERE club_id=? AND season=? AND week=?',(club_id,season,week)).fetchone())

    def overtraining_report(self, club_id: int, season: int, week: int) -> dict:
        plan=self.connection.execute('SELECT plan_id,load,status FROM training_plans WHERE club_id=? AND season=? AND week=?',(club_id,season,week)).fetchone()
        if not plan: return {'club_id':int(club_id),'risk':'UNKNOWN','players':[],'persisted':False}
        rows=self.connection.execute("SELECT player_id,load,recovery_days,injury_risk,status FROM training_sessions WHERE plan_id=? AND injury_risk>=0.6 ORDER BY injury_risk DESC",(plan['plan_id'],)).fetchall()
        return {'club_id':int(club_id),'season':int(season),'week':int(week),'risk':'HIGH' if rows else 'NORMAL','players':[dict(r) for r in rows],'persisted':False}

    def training_audit(self, club_id: int, plan_id: int | None = None) -> list[dict]:
        query='SELECT * FROM training_audit WHERE club_id=?'; args=[club_id]
        if plan_id is not None: query+=' AND plan_id=?'; args.append(plan_id)
        return [dict(r) for r in self.connection.execute(query+' ORDER BY audit_id',args).fetchall()]

    def create_weekly_plan(self, club_id: int, season: int, week: int, plan_type: str = "GENERAL", load: int = 50) -> dict:
        self._assert_club(club_id)
        if plan_type not in PLAN_TYPES:
            raise ValueError("TRAINING_PLAN_INVALID")
        load = max(0, min(100, int(load)))
        now = date.today().isoformat()
        with self.connection:
            existing = self.connection.execute("SELECT plan_id FROM training_plans WHERE club_id=? AND season=? AND week=?", (club_id, season, week)).fetchone()
            if existing:
                return self.plan_summary(int(existing["plan_id"]))
            cursor = self.connection.execute("INSERT INTO training_plans(club_id,season,week,plan_type,load,created_at) VALUES(?,?,?,?,?,?)", (club_id, season, week, plan_type, load, now))
            plan_id = int(cursor.lastrowid)
            players = self.connection.execute("SELECT player.jogador_id AS player_id FROM jogador_time membership JOIN jogadores player ON player.jogador_id=membership.jogador_id WHERE membership.time_id=? ORDER BY player.jogador_id", (club_id,)).fetchall()
            for player in players:
                player_id = int(player["player_id"])
                state = self.connection.execute("SELECT condition,fatigue FROM player_sport_state WHERE player_id=?", (player_id,)).fetchone()
                condition = int(state["condition"]) if state else 100
                fatigue = int(state["fatigue"]) if state else 0
                injury = self.connection.execute("SELECT 1 FROM injuries WHERE player_id=? AND status='ACTIVE' LIMIT 1", (player_id,)).fetchone()
                risk = min(1.0, max(0.0, load / 100 + fatigue / 200 + (0.35 if injury else 0) - self._medical_bonus(club_id)))
                recovery = 1 if plan_type == "REST" else max(0, int(round(load / 35 + fatigue / 50)))
                status = "BLOCKED_INJURY" if injury and plan_type != "REST" else "PLANNED"
                self.connection.execute("INSERT INTO training_sessions(plan_id,player_id,load,recovery_days,injury_risk,status) VALUES(?,?,?,?,?,?)", (plan_id, player_id, 0 if status == "BLOCKED_INJURY" else load, recovery, round(risk, 4), status))
            self.connection.execute("INSERT INTO training_history(club_id,event_type,event_date,payload) VALUES(?,?,?,?)", (club_id, "TRAINING_PLAN_CREATED", now, f'{{"plan_id":{plan_id},"season":{int(season)},"week":{int(week)},"plan_type":"{plan_type}","load":{load}}}'))
            self.connection.execute('INSERT INTO training_audit(club_id,plan_id,action,payload,created_at) VALUES(?,?,?,?,?)',(club_id,plan_id,'CREATE',f'{{"load":{load}}}',now))
        return self.plan_summary(plan_id)

    def _medical_bonus(self, club_id: int) -> float:
        row = self.connection.execute("SELECT AVG(level) AS level FROM staff_members WHERE club_id=? AND status='ativo' AND role='medico'", (club_id,)).fetchone()
        return min(0.15, float(row["level"] or 0) * 0.02) if row else 0.0

    def plan_summary(self, plan_id: int) -> dict:
        plan = self.connection.execute("SELECT * FROM training_plans WHERE plan_id=?", (plan_id,)).fetchone()
        if plan is None:
            raise ValueError("TRAINING_PLAN_NOT_FOUND")
        sessions = self.connection.execute("SELECT status,COUNT(*) AS total,AVG(injury_risk) AS risk FROM training_sessions WHERE plan_id=? GROUP BY status ORDER BY status", (plan_id,)).fetchall()
        return {**dict(plan), "sessions": [dict(row) for row in sessions], "medical_bonus": self._medical_bonus(int(plan["club_id"]))}

    def individual_development(self, club_id: int) -> list[dict]:
        self._assert_club(club_id)
        rows = self.connection.execute("""SELECT player.jogador_id AS player_id,player.nome AS name,player.cr2 AS potential,
            COALESCE(state.form,50) AS form,COALESCE(state.condition,100) AS condition,COALESCE(state.fatigue,0) AS fatigue,
            COALESCE(SUM(session.load),0) AS planned_load
            FROM jogador_time membership JOIN jogadores player ON player.jogador_id=membership.jogador_id
            LEFT JOIN player_sport_state state ON state.player_id=player.jogador_id
            LEFT JOIN training_sessions session ON session.player_id=player.jogador_id AND session.status='PLANNED'
            WHERE membership.time_id=? GROUP BY player.jogador_id ORDER BY player.nome COLLATE NOCASE""", (club_id,)).fetchall()
        return [{**dict(row), "performance_gap": round(max(0, int(row["potential"] or 0) - int(row["form"] or 0)), 2)} for row in rows]

    def create_objective(self, club_id: int, player_id: int, season: int, metric: str, target: float) -> dict:
        self._assert_club(club_id)
        if target <= 0 or not metric.strip():
            raise ValueError("TRAINING_OBJECTIVE_INVALID")
        with self.connection:
            row = self.connection.execute("SELECT objective_id FROM training_objectives WHERE club_id=? AND player_id=? AND season=? AND metric=?", (club_id, player_id, season, metric.strip())).fetchone()
            if row:
                return dict(self.connection.execute("SELECT * FROM training_objectives WHERE objective_id=?", (row["objective_id"],)).fetchone())
            cursor = self.connection.execute("INSERT INTO training_objectives(club_id,player_id,season,metric,target,created_at) VALUES(?,?,?,?,?,?)", (club_id, player_id, season, metric.strip(), float(target), date.today().isoformat()))
            return dict(self.connection.execute("SELECT * FROM training_objectives WHERE objective_id=?", (cursor.lastrowid,)).fetchone())

    def preview_plan(self, plan_id: int) -> dict:
        plan = self.connection.execute("SELECT * FROM training_plans WHERE plan_id=?", (plan_id,)).fetchone()
        if plan is None:
            raise ValueError("TRAINING_PLAN_NOT_FOUND")
        summary = self.plan_summary(plan_id)
        sessions = self.connection.execute("SELECT COALESCE(SUM(load),0) AS total_load, COALESCE(AVG(injury_risk),0) AS average_risk, COALESCE(SUM(recovery_days),0) AS recovery_days FROM training_sessions WHERE plan_id=?", (plan_id,)).fetchone()
        return {**summary, "preview": {"total_load": int(sessions["total_load"]), "average_risk": round(float(sessions["average_risk"]), 4), "recovery_days": int(sessions["recovery_days"]), "persisted": False, "formula_version": "training-plan-preview-v1"}}

    def approve_plan(self, plan_id: int, version: int = 1) -> dict:
        with self.connection:
            plan = self.connection.execute("SELECT * FROM training_plans WHERE plan_id=?", (plan_id,)).fetchone()
            if plan is None:
                raise ValueError("TRAINING_PLAN_NOT_FOUND")
            self.connection.execute("INSERT OR IGNORE INTO training_plan_versions(plan_id,version,author,status,created_at) VALUES(?,?,?,?,?)", (plan_id, version, "manager", "DRAFT", date.today().isoformat()))
            self.connection.execute("UPDATE training_plan_versions SET status='APPROVED' WHERE plan_id=? AND version=?", (plan_id, version))
            self.connection.execute("UPDATE training_plans SET status='APPROVED' WHERE plan_id=?", (plan_id,))
            self.connection.execute("UPDATE training_sessions SET status=CASE WHEN status='BLOCKED_INJURY' THEN status ELSE 'APPROVED' END WHERE plan_id=?", (plan_id,))
            return self.plan_summary(plan_id)

    def cancel_plan(self, plan_id: int, version: int = 1) -> dict:
        with self.connection:
            plan = self.connection.execute("SELECT * FROM training_plans WHERE plan_id=?", (plan_id,)).fetchone()
            if plan is None:
                raise ValueError("TRAINING_PLAN_NOT_FOUND")
            self.connection.execute("INSERT OR IGNORE INTO training_plan_versions(plan_id,version,author,status,created_at) VALUES(?,?,?,?,?)", (plan_id, version, "manager", "DRAFT", date.today().isoformat()))
            self.connection.execute("UPDATE training_plan_versions SET status='CANCELLED' WHERE plan_id=? AND version=?", (plan_id, version))
            self.connection.execute("UPDATE training_plans SET status='CANCELLED' WHERE plan_id=?", (plan_id,))
            self.connection.execute("UPDATE training_sessions SET status='CANCELLED' WHERE plan_id=? AND status NOT IN ('BLOCKED_INJURY', 'CANCELLED')", (plan_id,))
            return self.plan_summary(plan_id)

    def create_individual_plan(self, club_id: int, player_id: int, season: int, focus: str, weekly_load: int = 40) -> dict:
        self._assert_club(club_id)
        if not str(focus).strip() or not 0 <= int(weekly_load) <= 100: raise ValueError('INDIVIDUAL_PLAN_INVALID')
        member = self.connection.execute('SELECT jogador_id FROM jogador_time WHERE time_id=? AND jogador_id=?', (int(club_id), int(player_id))).fetchone()
        if member is None: raise ValueError('PLAYER_OUTSIDE_CLUB')
        state = self.connection.execute('SELECT condition,fatigue FROM player_sport_state WHERE player_id=?', (int(player_id),)).fetchone()
        condition, fatigue = (int(state['condition']), int(state['fatigue'])) if state else (100, 0)
        compatibility = round(max(0.0, min(1.0, (condition / 100) - (fatigue / 200))), 4)
        risk = round(max(0.0, min(1.0, int(weekly_load) / 100 + fatigue / 200 - self._medical_bonus(club_id))), 4)
        with self.connection:
            self.connection.execute('INSERT INTO individual_training_plans(club_id,player_id,season,focus,weekly_load,created_at) VALUES(?,?,?,?,?,?) ON CONFLICT(club_id,player_id,season,focus) DO UPDATE SET weekly_load=excluded.weekly_load', (int(club_id), int(player_id), int(season), str(focus).strip(), int(weekly_load), date.today().isoformat()))
            row = self.connection.execute('SELECT * FROM individual_training_plans WHERE club_id=? AND player_id=? AND season=? AND focus=?', (int(club_id), int(player_id), int(season), str(focus).strip())).fetchone()
            self.connection.execute('INSERT INTO individual_training_sessions(individual_plan_id,session_date,load,compatibility,risk) VALUES(?,?,?,?,?)', (int(row['individual_plan_id']), date.today().isoformat(), int(weekly_load), compatibility, risk))
        return {**dict(row), 'compatibility': compatibility, 'risk': risk}

    def preview_individual_plan(self, individual_plan_id: int) -> dict:
        row = self.connection.execute('SELECT * FROM individual_training_plans WHERE individual_plan_id=?', (int(individual_plan_id),)).fetchone()
        if row is None: raise ValueError('INDIVIDUAL_PLAN_NOT_FOUND')
        sessions = self.connection.execute('SELECT COALESCE(SUM(load),0) AS total_load,COALESCE(AVG(compatibility),0) AS compatibility,COALESCE(AVG(risk),0) AS risk FROM individual_training_sessions WHERE individual_plan_id=?', (int(individual_plan_id),)).fetchone()
        return {**dict(row), 'preview': {'total_load': int(sessions['total_load']), 'compatibility': round(float(sessions['compatibility']), 4), 'risk': round(float(sessions['risk']), 4), 'persisted': False, 'formula_version': 'individual-training-preview-v1'}}

    def approve_individual_plan(self, individual_plan_id: int) -> dict:
        row = self.connection.execute('SELECT * FROM individual_training_plans WHERE individual_plan_id=?', (int(individual_plan_id),)).fetchone()
        if row is None: raise ValueError('INDIVIDUAL_PLAN_NOT_FOUND')
        risk = self.connection.execute('SELECT AVG(risk) AS risk FROM individual_training_sessions WHERE individual_plan_id=?', (int(individual_plan_id),)).fetchone()['risk'] or 0
        status = 'BLOCKED_MEDICAL_RISK' if float(risk) >= 0.85 else 'APPROVED'
        with self.connection:
            self.connection.execute('UPDATE individual_training_plans SET status=? WHERE individual_plan_id=?', (status, int(individual_plan_id)))
            self.connection.execute('UPDATE individual_training_sessions SET status=? WHERE individual_plan_id=?', ('BLOCKED_MEDICAL_RISK' if status != 'APPROVED' else 'APPROVED', int(individual_plan_id)))
            self.connection.execute('INSERT INTO training_history(club_id,event_type,event_date,payload) VALUES(?,?,?,?)', (row['club_id'], 'INDIVIDUAL_PLAN_APPROVED' if status == 'APPROVED' else 'INDIVIDUAL_PLAN_BLOCKED', date.today().isoformat(), f'{{"individual_plan_id":{individual_plan_id},"status":"{status}"}}'))
        return dict(self.connection.execute('SELECT * FROM individual_training_plans WHERE individual_plan_id=?', (int(individual_plan_id),)).fetchone())

    def record_evolution(self, club_id: int, player_id: int, season: int, delta: float, source: str, reference: str) -> dict:
        if not source.strip() or not reference.strip(): raise ValueError('EVOLUTION_SOURCE_REQUIRED')
        self._assert_club(club_id)
        self.connection.execute('INSERT OR IGNORE INTO training_evolution_history(club_id,player_id,season,source,delta,created_at,reference) VALUES(?,?,?,?,?,?,?)', (int(club_id), int(player_id), int(season), source.strip(), float(delta), date.today().isoformat(), reference.strip()))
        self.connection.commit()
        row = self.connection.execute('SELECT * FROM training_evolution_history WHERE reference=?', (reference.strip(),)).fetchone()
        return dict(row)

    def maintenance_alerts(self, club_id: int) -> list[dict]:
        return [{"department": item["department"], "message": "Departamento sem manutenção persistida."} for item in self.department_inventory(club_id) if item["level"] > 0 and item["maintenance"] <= 0]

    def budget(self, club_id: int) -> list[dict]:
        inventory = {item["department"]: item for item in self.department_inventory(club_id)}
        result = []
        for name, rule in DEPARTMENTS.items():
            item = inventory[name]
            if item["level"] >= 10:
                continue
            next_level = item["level"] + 1
            result.append({"department": name, "next_level": next_level, "cost": int(rule["purchase"] * next_level), "projected_capacity": int(rule["capacity"] * next_level), "maintenance": int(rule["maintenance"] * next_level)})
        return result
