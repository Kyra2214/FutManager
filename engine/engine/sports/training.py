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
