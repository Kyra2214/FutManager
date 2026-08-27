from __future__ import annotations

import json
import random
import sqlite3
from datetime import date
from pathlib import Path

from engine.core.state_store import assert_mutable_state_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS player_morale(player_id INTEGER PRIMARY KEY,club_id INTEGER NOT NULL,morale INTEGER NOT NULL DEFAULT 50,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS form_history(history_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,player_id INTEGER,event_type TEXT NOT NULL,delta INTEGER NOT NULL,season INTEGER,week INTEGER,seed INTEGER,payload TEXT NOT NULL,event_date TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS morale_history(history_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,event_type TEXT NOT NULL,delta REAL NOT NULL,season INTEGER,week INTEGER,seed INTEGER,payload TEXT NOT NULL,event_date TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS opponent_preparation(preparation_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,opponent_id INTEGER NOT NULL,season INTEGER NOT NULL,week INTEGER NOT NULL,focus TEXT NOT NULL,adherence INTEGER NOT NULL DEFAULT 0,UNIQUE(club_id,opponent_id,season,week));
CREATE INDEX IF NOT EXISTS idx_form_history_club_week ON form_history(club_id,season,week);
CREATE INDEX IF NOT EXISTS idx_morale_history_club_week ON morale_history(club_id,season,week);
"""

TRAINING_DELTAS = {"TECHNICAL": 3, "TACTICAL": 2, "PHYSICAL": 1, "SET_PIECES": 2, "GENERAL": 1, "REST": 0}


class FormMoraleService:
    def __init__(self, database: str | Path | sqlite3.Connection):
        if isinstance(database, sqlite3.Connection):
            self.connection = database
        else:
            assert_mutable_state_path(database)
            self.connection = sqlite3.connect(str(database))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(SCHEMA)
        columns = {row["name"] for row in self.connection.execute("PRAGMA table_info(player_sport_state)").fetchall()}
        for column in ("technical_form", "physical_form"):
            if column not in columns:
                self.connection.execute(f"ALTER TABLE player_sport_state ADD COLUMN {column} INTEGER NOT NULL DEFAULT 50")
        self.connection.commit()

    def close(self):
        self.connection.close()

    def _assert_club(self, club_id: int):
        if self.connection.execute("SELECT 1 FROM times WHERE time_id=?", (int(club_id),)).fetchone() is None:
            raise ValueError("CLUB_NOT_FOUND")

    def _players(self, club_id: int):
        return self.connection.execute("SELECT j.jogador_id AS player_id,COALESCE(j.idade,25) AS age,COALESCE(s.form,50) AS form,COALESCE(s.technical_form,s.form,50) AS technical_form,COALESCE(s.physical_form,s.form,50) AS physical_form,COALESCE(s.fatigue,0) AS fatigue,COALESCE(s.condition,100) AS condition FROM jogador_time jt JOIN jogadores j ON j.jogador_id=jt.jogador_id LEFT JOIN player_sport_state s ON s.player_id=j.jogador_id WHERE jt.time_id=? ORDER BY j.jogador_id", (club_id,)).fetchall()

    def _ensure_morale(self, club_id: int, player_id: int) -> int:
        row = self.connection.execute("SELECT morale FROM player_morale WHERE player_id=?", (player_id,)).fetchone()
        if row:
            return int(row["morale"])
        self.connection.execute("INSERT INTO player_morale(player_id,club_id,morale,updated_at) VALUES(?,?,?,?)", (player_id, club_id, 50, date.today().isoformat()))
        return 50

    def collective_morale(self, club_id: int) -> dict:
        self._assert_club(club_id)
        players = self._players(club_id)
        values = [self._ensure_morale(club_id, int(p["player_id"])) for p in players]
        self.connection.commit()
        return {"club_id": club_id, "average": round(sum(values) / len(values), 2) if values else 0.0, "members": len(values), "lowest": min(values) if values else 0, "highest": max(values) if values else 0}

    def update_after_match(self, club_id: int, result: str, season: int, week: int, seed: int | None = None) -> dict:
        self._assert_club(club_id)
        if result not in {"WIN", "DRAW", "LOSS"}:
            raise ValueError("MATCH_RESULT_INVALID")
        delta = {"WIN": 5, "DRAW": 0, "LOSS": -5}[result]
        players = self._players(club_id)
        with self.connection:
            for player in players:
                pid = int(player["player_id"]); old_form = int(player["form"]); old_morale = self._ensure_morale(club_id, pid)
                jitter = random.Random((seed or 0) + pid + season * 1000 + week).choice([-1, 0, 1])
                new_form = max(0, min(100, old_form + delta // 2 + jitter))
                new_technical = max(0, min(100, int(player["technical_form"]) + delta // 2 + jitter))
                new_physical = max(0, min(100, int(player["physical_form"]) + delta // 2 + jitter))
                new_morale = max(0, min(100, old_morale + delta))
                self.connection.execute("UPDATE player_sport_state SET form=?,technical_form=?,physical_form=?,last_updated=? WHERE player_id=?", (new_form, new_technical, new_physical, date.today().isoformat(), pid))
                self.connection.execute("UPDATE player_morale SET morale=?,updated_at=? WHERE player_id=?", (new_morale, date.today().isoformat(), pid))
                self.connection.execute("INSERT INTO form_history(club_id,player_id,event_type,delta,season,week,seed,payload,event_date) VALUES(?,?,?,?,?,?,?,?,?)", (club_id, pid, "MATCH_RESULT", new_form - old_form, season, week, seed, json.dumps({"result": result, "old_form": old_form, "new_form": new_form}), date.today().isoformat()))
            self.connection.execute("INSERT INTO morale_history(club_id,event_type,delta,season,week,seed,payload,event_date) VALUES(?,?,?,?,?,?,?,?)", (club_id, "MATCH_RESULT", delta, season, week, seed, json.dumps({"result": result}), date.today().isoformat()))
        return self.collective_morale(club_id)

    def create_opponent_preparation(self, club_id: int, opponent_id: int, season: int, week: int, focus: str) -> dict:
        self._assert_club(club_id)
        if not focus.strip():
            raise ValueError("PREPARATION_FOCUS_REQUIRED")
        with self.connection:
            self.connection.execute("INSERT INTO opponent_preparation(club_id,opponent_id,season,week,focus) VALUES(?,?,?,?,?) ON CONFLICT(club_id,opponent_id,season,week) DO UPDATE SET focus=excluded.focus", (club_id, opponent_id, season, week, focus.strip()))
        return dict(self.connection.execute("SELECT * FROM opponent_preparation WHERE club_id=? AND opponent_id=? AND season=? AND week=?", (club_id, opponent_id, season, week)).fetchone())

    def apply_weekly_training(self, club_id: int, season: int, week: int, plan_type: str, load: int, seed: int | None = None, international_matches: int = 0) -> dict:
        self._assert_club(club_id)
        if plan_type not in TRAINING_DELTAS:
            raise ValueError("TRAINING_TYPE_INVALID")
        changes = []
        with self.connection:
            for player in self._players(club_id):
                pid = int(player["player_id"]); age = int(player["age"]); old_form = int(player["form"]); old_fatigue = int(player["fatigue"])
                age_penalty = max(0, age - 28) // 4
                international_penalty = min(20, max(0, int(international_matches)) * 4)
                effective_load = 0 if plan_type == "REST" else min(100, max(0, int(load) - age_penalty - international_penalty))
                fatigue_delta = -12 if plan_type == "REST" else max(1, effective_load // 12)
                fatigue_delta += international_penalty // 4
                new_fatigue = max(0, min(100, old_fatigue + fatigue_delta))
                form_delta = TRAINING_DELTAS[plan_type] if plan_type != "REST" else 1
                new_form = max(0, min(100, old_form + form_delta + random.Random((seed or 0) + pid).choice([-1, 0, 1])))
                technical = int(player["technical_form"]); physical = int(player["physical_form"])
                new_technical = max(0, min(100, technical + (form_delta if plan_type in {"TECHNICAL", "TACTICAL", "SET_PIECES"} else 0)))
                new_physical = max(0, min(100, physical + (form_delta if plan_type == "PHYSICAL" else 0)))
                self.connection.execute("UPDATE player_sport_state SET form=?,technical_form=?,physical_form=?,fatigue=?,last_updated=? WHERE player_id=?", (new_form, new_technical, new_physical, new_fatigue, date.today().isoformat(), pid))
                changes.append({"player_id": pid, "form_delta": new_form-old_form, "fatigue_delta": new_fatigue-old_fatigue, "effective_load": effective_load, "adherence": 100 if effective_load == load or plan_type == "REST" else round(effective_load / max(1, load) * 100)})
                self.connection.execute("INSERT INTO form_history(club_id,player_id,event_type,delta,season,week,seed,payload,event_date) VALUES(?,?,?,?,?,?,?,?,?)", (club_id, pid, "WEEKLY_TRAINING", new_form-old_form, season, week, seed, json.dumps(changes[-1]), date.today().isoformat()))
        return {"club_id": club_id, "season": season, "week": week, "plan_type": plan_type, "load": load, "changes": changes, "collective_morale": self.collective_morale(club_id)}

    def weekly_load_report(self, club_id: int, season: int, week: int) -> dict:
        self._assert_club(club_id)
        rows = self.connection.execute("SELECT player_id,SUM(CASE WHEN event_type='WEEKLY_TRAINING' THEN json_extract(payload,'$.effective_load') ELSE 0 END) AS load,AVG(CASE WHEN event_type='WEEKLY_TRAINING' THEN json_extract(payload,'$.adherence') END) AS adherence FROM form_history WHERE club_id=? AND season=? AND week=? GROUP BY player_id ORDER BY player_id", (club_id, season, week)).fetchall()
        return {"club_id": club_id, "season": season, "week": week, "players": [dict(row) for row in rows], "total_load": sum(int(row["load"] or 0) for row in rows)}

    def recommendations(self, club_id: int) -> list[dict]:
        self._assert_club(club_id)
        result = []
        for player in self._players(club_id):
            if int(player["fatigue"]) >= 70:
                result.append({"player_id": int(player["player_id"]), "type": "REST", "reason": "fadiga elevada persistida"})
            elif int(player["condition"]) < 60:
                result.append({"player_id": int(player["player_id"]), "type": "RECOVERY", "reason": "condição física abaixo do limite"})
            elif int(player["form"]) < 45:
                result.append({"player_id": int(player["player_id"]), "type": "TECHNICAL", "reason": "forma técnica abaixo do limite"})
        return result
