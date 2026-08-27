from __future__ import annotations

import json
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from engine.core.state_store import assert_mutable_state_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS medical_history(history_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,player_id INTEGER NOT NULL,event_type TEXT NOT NULL,event_date TEXT NOT NULL,payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS health_alerts(alert_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,player_id INTEGER NOT NULL,alert_type TEXT NOT NULL,message TEXT NOT NULL,created_at TEXT NOT NULL,read INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS idx_medical_history_player ON medical_history(player_id,event_date);
CREATE INDEX IF NOT EXISTS idx_health_alerts_club ON health_alerts(club_id,read,created_at);
CREATE TABLE IF NOT EXISTS injury_catalog(injury_code TEXT PRIMARY KEY, severity TEXT NOT NULL, default_days INTEGER NOT NULL, body_area TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS medical_reassessments(reassessment_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,player_id INTEGER NOT NULL,injury_id INTEGER NOT NULL,due_date TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'SCHEDULED',notes TEXT NOT NULL DEFAULT '',UNIQUE(injury_id,due_date));
CREATE TABLE IF NOT EXISTS injury_relapses(relapse_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,player_id INTEGER NOT NULL,previous_injury_id INTEGER NOT NULL,new_injury_id INTEGER,created_at TEXT NOT NULL,reference TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS medical_treatments(treatment_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,player_id INTEGER NOT NULL,treatment_type TEXT NOT NULL,cost INTEGER NOT NULL,recovery_delta INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'APPLIED',created_at TEXT NOT NULL,reference TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS medical_return_protocols(player_id INTEGER PRIMARY KEY,club_id INTEGER NOT NULL,minutes_limit INTEGER NOT NULL DEFAULT 0,risk REAL NOT NULL DEFAULT 0.0,clearance TEXT NOT NULL DEFAULT 'BLOCKED',updated_at TEXT NOT NULL);
"""
SEVERITY_DAYS = {"MINOR": 5, "MODERATE": 14, "SEVERE": 35}


class HealthService:
    def __init__(self, database: str | Path | sqlite3.Connection):
        if isinstance(database, sqlite3.Connection): self.connection = database
        else:
            assert_mutable_state_path(database); self.connection = sqlite3.connect(str(database))
        self.connection.row_factory = sqlite3.Row; self.connection.execute("PRAGMA foreign_keys=ON"); self.connection.executescript(SCHEMA)
        columns = {row["name"] for row in self.connection.execute("PRAGMA table_info(injuries)").fetchall()}
        if "diagnosis" not in columns: self.connection.execute("ALTER TABLE injuries ADD COLUMN diagnosis TEXT NOT NULL DEFAULT ''")
        self.connection.commit()

    def close(self): self.connection.close()

    def _player(self, club_id: int, player_id: int):
        row = self.connection.execute("SELECT j.jogador_id AS player_id,j.nome AS name,COALESCE(j.idade,25) AS age,COALESCE(s.condition,100) AS condition,COALESCE(s.recovery_days,0) AS recovery_days FROM jogador_time jt JOIN jogadores j ON j.jogador_id=jt.jogador_id LEFT JOIN player_sport_state s ON s.player_id=j.jogador_id WHERE jt.time_id=? AND j.jogador_id=?", (club_id, player_id)).fetchone()
        if row is None: raise ValueError("PLAYER_OUTSIDE_CLUB")
        return row

    def _medical_bonus(self, club_id: int) -> float:
        row = self.connection.execute("SELECT AVG(level) AS level FROM staff_members WHERE club_id=? AND status='ativo' AND role='medico'", (club_id,)).fetchone()
        return min(0.25, float(row["level"] or 0) * 0.03) if row else 0.0

    def injury_catalog(self) -> list[dict]:
        for code, severity, days, area in (("MUSCULAR", "MINOR", 5, "muscular"), ("KNEE", "SEVERE", 35, "joelho"), ("ANKLE", "MODERATE", 14, "tornozelo")):
            self.connection.execute('INSERT OR IGNORE INTO injury_catalog(injury_code,severity,default_days,body_area) VALUES(?,?,?,?)', (code, severity, days, area))
        self.connection.commit()
        return [dict(row) for row in self.connection.execute('SELECT * FROM injury_catalog ORDER BY injury_code').fetchall()]

    def preview_return(self, club_id: int, player_id: int) -> dict:
        player = self._player(club_id, player_id)
        injury = self.connection.execute("SELECT * FROM injuries WHERE player_id=? AND status='ACTIVE' ORDER BY injury_id DESC LIMIT 1", (player_id,)).fetchone()
        if injury is None: return {'club_id': club_id, 'player_id': player_id, 'available': True, 'estimated_return': None, 'risk': 0.0, 'persisted': False}
        risk = round(max(0.0, min(1.0, int(player['recovery_days']) / max(1, int(injury['estimated_days'])))), 4)
        return {'club_id': club_id, 'player_id': player_id, 'available': False, 'estimated_return': injury['end_date'], 'risk': risk, 'persisted': False}

    def schedule_reassessment(self, club_id: int, player_id: int, due_date: str, notes: str = '') -> dict:
        self._player(club_id, player_id)
        injury = self.connection.execute("SELECT injury_id FROM injuries WHERE player_id=? AND status='ACTIVE' ORDER BY injury_id DESC LIMIT 1", (player_id,)).fetchone()
        if injury is None: raise ValueError('ACTIVE_INJURY_NOT_FOUND')
        self.connection.execute('INSERT OR IGNORE INTO medical_reassessments(club_id,player_id,injury_id,due_date,notes) VALUES(?,?,?,?,?)', (club_id, player_id, injury['injury_id'], due_date, notes)); self.connection.commit()
        return dict(self.connection.execute('SELECT * FROM medical_reassessments WHERE injury_id=? AND due_date=?', (injury['injury_id'], due_date)).fetchone())

    def set_return_protocol(self, club_id: int, player_id: int, minutes_limit: int, risk: float, clearance: str = 'LIMITED') -> dict:
        self._player(club_id,player_id)
        if int(minutes_limit)<0 or not 0<=float(risk)<=1 or clearance not in ('BLOCKED','LIMITED','CLEARED'): raise ValueError('RETURN_PROTOCOL_INVALID')
        with self.connection: self.connection.execute('INSERT OR REPLACE INTO medical_return_protocols(player_id,club_id,minutes_limit,risk,clearance,updated_at) VALUES(?,?,?,?,?,?)',(player_id,club_id,minutes_limit,risk,clearance,date.today().isoformat()))
        return dict(self.connection.execute('SELECT * FROM medical_return_protocols WHERE player_id=?',(player_id,)).fetchone())

    def selection_eligibility(self, club_id: int, player_id: int) -> dict:
        self._player(club_id,player_id)
        injury=self.connection.execute("SELECT 1 FROM injuries WHERE player_id=? AND status='ACTIVE'",(player_id,)).fetchone()
        protocol=self.connection.execute('SELECT * FROM medical_return_protocols WHERE player_id=?',(player_id,)).fetchone()
        eligible=not injury and (not protocol or protocol['clearance']=='CLEARED')
        return {'club_id':int(club_id),'player_id':int(player_id),'eligible':eligible,'minutes_limit':int(protocol['minutes_limit']) if protocol else 90,'clearance':protocol['clearance'] if protocol else 'CLEARED','persisted':False}

    def apply_treatment(self, club_id: int, player_id: int, treatment_type: str, cost: int, recovery_delta: int, reference: str) -> dict:
        self._player(club_id,player_id)
        if int(cost)<0 or int(recovery_delta)<0 or not str(reference).strip(): raise ValueError('TREATMENT_INVALID')
        with self.connection: self.connection.execute('INSERT OR IGNORE INTO medical_treatments(club_id,player_id,treatment_type,cost,recovery_delta,created_at,reference) VALUES(?,?,?,?,?,?,?)',(club_id,player_id,treatment_type,cost,recovery_delta,date.today().isoformat(),reference))
        return dict(self.connection.execute('SELECT * FROM medical_treatments WHERE reference=?',(reference,)).fetchone())

    def clinical_audit(self, club_id: int, player_id: int | None = None) -> dict:
        query='SELECT * FROM medical_history WHERE club_id=?'; args=[club_id]
        if player_id is not None: query+=' AND player_id=?'; args.append(player_id)
        return {'club_id':int(club_id),'history':[dict(r) for r in self.connection.execute(query+' ORDER BY history_id',args).fetchall()],'treatments':[dict(r) for r in self.connection.execute('SELECT * FROM medical_treatments WHERE club_id=? ORDER BY treatment_id',(club_id,)).fetchall()],'persisted':True}

    def register_injury(self, club_id: int, player_id: int, injury_type: str, severity: str, season: int, week: int, seed: int | None = None) -> dict:
        player = self._player(club_id, player_id); severity = severity.upper()
        if severity not in SEVERITY_DAYS: raise ValueError("INJURY_SEVERITY_INVALID")
        existing = self.connection.execute("SELECT injury_id FROM injuries WHERE player_id=? AND status='ACTIVE'", (player_id,)).fetchone()
        if existing: raise ValueError("INJURY_ALREADY_ACTIVE")
        jitter = random.Random((seed or 0) + player_id + season * 97 + week).randint(-2, 2)
        days = max(1, int(round(SEVERITY_DAYS[severity] * (1 - self._medical_bonus(club_id)) + jitter)))
        start = date.today(); end = start + timedelta(days=days)
        with self.connection:
            cur = self.connection.execute("INSERT INTO injuries(player_id,injury_type,start_date,estimated_days,end_date,severity,status,diagnosis) VALUES(?,?,?,?,?,?,?,?)", (player_id, injury_type, start.isoformat(), days, end.isoformat(), severity, "ACTIVE", injury_type))
            self.connection.execute("UPDATE player_sport_state SET available=0,current_injury_id=?,recovery_days=?,last_updated=? WHERE player_id=?", (cur.lastrowid, days, start.isoformat(), player_id))
            payload = json.dumps({"injury_id": cur.lastrowid, "type": injury_type, "severity": severity, "estimated_days": days, "return_date": end.isoformat()})
            self.connection.execute("INSERT INTO medical_history(club_id,player_id,event_type,event_date,payload) VALUES(?,?,?,?,?)", (club_id, player_id, "INJURY_DIAGNOSED", start.isoformat(), payload))
            self.connection.execute("INSERT OR IGNORE INTO health_alerts(club_id,player_id,alert_type,message,created_at) VALUES(?,?,?,?,?)", (club_id, player_id, "NEW_INJURY", f"{player['name']}: {injury_type} ({severity}); retorno estimado em {days} dias.", start.isoformat()))
            previous = self.connection.execute("SELECT injury_id FROM injuries WHERE player_id=? AND injury_id<>? ORDER BY injury_id DESC LIMIT 1", (player_id, cur.lastrowid)).fetchone()
            if previous:
                self.connection.execute('INSERT OR IGNORE INTO injury_relapses(club_id,player_id,previous_injury_id,new_injury_id,created_at,reference) VALUES(?,?,?,?,?,?)', (club_id, player_id, previous['injury_id'], cur.lastrowid, start.isoformat(), f'relapse:{player_id}:{cur.lastrowid}'))
        return {"injury_id": int(cur.lastrowid), "player_id": player_id, "severity": severity, "estimated_days": days, "return_date": end.isoformat(), "medical_bonus": self._medical_bonus(club_id)}

    def recover(self, club_id: int, days: int = 1) -> list[dict]:
        self._assert_club(club_id); days = max(1, int(days)); recovered = []; effective_days = max(1, int(round(days * (1 + self._medical_bonus(club_id)))));
        rows = self.connection.execute("SELECT i.*,j.nome AS name FROM injuries i JOIN jogador_time jt ON jt.jogador_id=i.player_id JOIN jogadores j ON j.jogador_id=i.player_id WHERE jt.time_id=? AND i.status='ACTIVE'", (club_id,)).fetchall()
        with self.connection:
            for injury in rows:
                remaining = max(0, int(injury["estimated_days"]) - effective_days)
                if remaining == 0:
                    self.connection.execute("UPDATE injuries SET status='RECOVERED',end_date=? WHERE injury_id=?", (date.today().isoformat(), injury["injury_id"]))
                    self.connection.execute("UPDATE player_sport_state SET available=1,current_injury_id=NULL,recovery_days=0,last_updated=? WHERE player_id=?", (date.today().isoformat(), injury["player_id"]))
                    self.connection.execute("INSERT INTO health_alerts(club_id,player_id,alert_type,message,created_at) VALUES(?,?,?,?,?)", (club_id, injury["player_id"], "RETURNED", f"{injury['name']} retornou ao elenco.", date.today().isoformat()))
                    event = "RETURNED"
                else:
                    self.connection.execute("UPDATE injuries SET estimated_days=? WHERE injury_id=?", (remaining, injury["injury_id"]))
                    self.connection.execute("UPDATE player_sport_state SET recovery_days=?,last_updated=? WHERE player_id=?", (remaining, date.today().isoformat(), injury["player_id"]))
                    event = "RECOVERY_PROGRESS"
                self.connection.execute("INSERT INTO medical_history(club_id,player_id,event_type,event_date,payload) VALUES(?,?,?,?,?)", (club_id, injury["player_id"], event, date.today().isoformat(), json.dumps({"injury_id": injury["injury_id"], "remaining_days": remaining})))
                recovered.append({"player_id": int(injury["player_id"]), "remaining_days": remaining, "status": event})
        return recovered

    def register_suspension(self, club_id: int, player_id: int, cards: int, red_card: bool, season: int, week: int) -> dict:
        player = self._player(club_id, player_id); matches = 3 if red_card else max(1, min(3, int(cards)))
        until = date.today() + timedelta(days=matches * 7)
        with self.connection:
            self.connection.execute("INSERT INTO player_suspensions(player_id,until_date,reason,active,created_at) VALUES(?,?,?,?,?) ON CONFLICT(player_id) DO UPDATE SET until_date=excluded.until_date,reason=excluded.reason,active=1", (player_id, until.isoformat(), "EXPULSÃO" if red_card else f"{cards} cartão(ões)", 1, date.today().isoformat()))
            self.connection.execute("INSERT INTO medical_history(club_id,player_id,event_type,event_date,payload) VALUES(?,?,?,?,?)", (club_id, player_id, "SUSPENSION_REGISTERED", date.today().isoformat(), json.dumps({"matches": matches, "red_card": red_card, "season": season, "week": week})))
        return {"player_id": player_id, "matches": matches, "until_date": until.isoformat(), "reason": "EXPULSÃO" if red_card else f"{cards} cartão(ões)"}

    def list_health(self, club_id: int, severity: str | None = None, max_days: int | None = None) -> list[dict]:
        self._assert_club(club_id); query = "SELECT i.*,j.nome AS player_name FROM injuries i JOIN jogador_time jt ON jt.jogador_id=i.player_id JOIN jogadores j ON j.jogador_id=i.player_id WHERE jt.time_id=? AND i.status='ACTIVE'"; args: list[object] = [club_id]
        if severity: query += " AND i.severity=?"; args.append(severity.upper())
        if max_days is not None: query += " AND i.estimated_days<=?"; args.append(int(max_days))
        return [dict(row) for row in self.connection.execute(query + " ORDER BY i.estimated_days,i.player_id", args).fetchall()]

    def alerts(self, club_id: int) -> list[dict]:
        self._assert_club(club_id); return [dict(row) for row in self.connection.execute("SELECT * FROM health_alerts WHERE club_id=? AND read=0 ORDER BY alert_id DESC", (club_id,)).fetchall()]

    def _assert_club(self, club_id: int):
        if self.connection.execute("SELECT 1 FROM times WHERE time_id=?", (club_id,)).fetchone() is None: raise ValueError("CLUB_NOT_FOUND")
