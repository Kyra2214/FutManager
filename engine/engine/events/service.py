from __future__ import annotations

from contextlib import nullcontext
from datetime import date
from pathlib import Path
import sqlite3


from engine.core.state_store import assert_mutable_state_path
EVENT_TYPES = frozenset({"TRANSFERENCIA", "LESAO", "CONTRATO", "PATROCINIO", "FINANCEIRO", "COMPETICAO", "ESTADIO", "TORCIDA", "NOTICIA_PARTIDA", "NOTICIA_CONTRATACAO", "NOTICIA_SAUDE"})
SEVERITIES = {"LOW": 1, "NORMAL": 2, "HIGH": 3, "CRITICAL": 4}
SEVERITY_LABELS = {value: key for key, value in SEVERITIES.items()}

SCHEMA = """
CREATE TABLE IF NOT EXISTS club_events(
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  club_id INTEGER NOT NULL,
  type TEXT NOT NULL,
  origin TEXT,
  severity INTEGER NOT NULL,
  event_date TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  impact TEXT,
  status TEXT NOT NULL DEFAULT 'OPEN',
  reference TEXT UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_club_events_club_status_date ON club_events(club_id,status,event_id DESC);
CREATE TABLE IF NOT EXISTS notification_preferences(club_id INTEGER NOT NULL,event_type TEXT NOT NULL,enabled INTEGER NOT NULL DEFAULT 1,updated_at TEXT NOT NULL,PRIMARY KEY(club_id,event_type));
CREATE TABLE IF NOT EXISTS notification_snoozes(event_id INTEGER PRIMARY KEY,snoozed_until TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS notification_groups(group_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,group_key TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(club_id,group_key));
"""


class ClubEventService:
    """Fonte única para o feed de alertas; `reference` impede notificações duplicadas."""

    def __init__(self, database: str | Path | sqlite3.Connection):
        assert_mutable_state_path(database) if not isinstance(database, sqlite3.Connection) else None
        self.connection = sqlite3.connect(str(database)) if not isinstance(database, sqlite3.Connection) else database
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def record(
        self,
        club_id: int,
        event_type: str,
        severity: str,
        title: str,
        description: str,
        reference: str,
        *,
        origin: str,
        event_date: date | str | None = None,
        impact: str | None = None,
        managed_transaction: bool = True,
    ) -> bool:
        normalized_type = str(event_type).upper()
        normalized_severity = str(severity).upper()
        if normalized_type not in EVENT_TYPES:
            raise ValueError("EVENT_TYPE_INVALID")
        if normalized_severity not in SEVERITIES:
            raise ValueError("EVENT_SEVERITY_INVALID")
        event_day = event_date.isoformat() if isinstance(event_date, date) else str(event_date or date.today().isoformat())
        with (self.connection if managed_transaction else nullcontext()):
            cursor = self.connection.execute(
                """INSERT OR IGNORE INTO club_events(club_id,type,origin,severity,event_date,title,description,impact,status,reference)
                   VALUES(?,?,?,?,?,?,?,?, 'OPEN', ?)""",
                (club_id, normalized_type, origin, SEVERITIES[normalized_severity], event_day, title, description, impact, reference),
            )
        return bool(cursor.rowcount)

    def list_for_club(self, club_id: int, limit: int = 20, unread_only: bool = False) -> dict:
        safe_limit = min(max(int(limit), 1), 100)
        query = "SELECT * FROM club_events WHERE club_id=?"
        params: list[object] = [club_id]
        if unread_only:
            query += " AND status='OPEN'"
        query += " ORDER BY CASE severity WHEN 4 THEN 0 WHEN 3 THEN 1 WHEN 2 THEN 2 ELSE 3 END,event_id DESC LIMIT ?"
        params.append(safe_limit)
        rows = self.connection.execute(query, params).fetchall()
        unread = self.connection.execute("SELECT COUNT(*) FROM club_events WHERE club_id=? AND status='OPEN'", (club_id,)).fetchone()[0]
        return {
            "unread_count": int(unread),
            "items": [
                {
                    "event_id": int(row["event_id"]),
                    "club_id": int(row["club_id"]),
                    "type": str(row["type"]),
                    "origin": row["origin"],
                    "severity": SEVERITY_LABELS.get(int(row["severity"]), "NORMAL"),
                    "event_date": str(row["event_date"]),
                    "title": str(row["title"]),
                    "description": row["description"],
                    "impact": row["impact"],
                    "status": str(row["status"]),
                    "is_read": str(row["status"]) == "READ",
                    "reference": row["reference"],
                }
                for row in rows
            ],
        }

    def news_catalog(self) -> list[dict]:
        return [{'type':'NOTICIA_PARTIDA','label':'Partida oficial','origin_required':True},{'type':'NOTICIA_CONTRATACAO','label':'Contratação ou renovação','origin_required':True},{'type':'NOTICIA_SAUDE','label':'Lesão ou retorno','origin_required':True}]

    def generate_match_news(self, club_id, match_id, title, description, severity='NORMAL'):
        return self.record(club_id,'NOTICIA_PARTIDA',severity,title,description,f'match:{match_id}',origin=f'fixture:{match_id}')

    def generate_contract_news(self, club_id, contract_id, title, description, severity='NORMAL'):
        return self.record(club_id,'NOTICIA_CONTRATACAO',severity,title,description,f'contract:{contract_id}',origin=f'contract:{contract_id}')

    def generate_health_news(self, club_id, health_event_id, title, description, severity='NORMAL'):
        return self.record(club_id,'NOTICIA_SAUDE',severity,title,description,f'health:{health_event_id}',origin=f'health:{health_event_id}')

    def news_feed(self, club_id: int, limit: int = 20, cursor: int | None = None, type_: str | None = None, severity: str | None = None) -> dict:
        safe_limit=min(max(int(limit),1),100); query='SELECT * FROM club_events WHERE club_id=? AND type LIKE \'NOTICIA_%\''; params=[int(club_id)]
        if cursor is not None: query+=' AND event_id<?'; params.append(int(cursor))
        disabled=self.connection.execute('SELECT event_type FROM notification_preferences WHERE club_id=? AND enabled=0',(int(club_id),)).fetchall()
        if disabled:
            blocked=[str(row['event_type']) for row in disabled]; query+=' AND type NOT IN ('+','.join('?' for _ in blocked)+')'; params.extend(blocked)
        if type_: query+=' AND type=?'; params.append(str(type_).upper())
        if severity: query+=' AND severity=?'; params.append(SEVERITIES.get(str(severity).upper(),-1))
        rows=self.connection.execute(query+' ORDER BY event_id DESC LIMIT ?',params+[safe_limit]).fetchall()
        return {'items':[dict(row) for row in rows],'next_cursor':int(rows[-1]['event_id']) if len(rows)==safe_limit else None,'count':len(rows)}

    def set_preference(self, club_id: int, event_type: str, enabled: bool) -> dict:
        with self.connection:
            self.connection.execute('INSERT INTO notification_preferences(club_id,event_type,enabled,updated_at) VALUES(?,?,?,?) ON CONFLICT(club_id,event_type) DO UPDATE SET enabled=excluded.enabled,updated_at=excluded.updated_at',(int(club_id),str(event_type).upper(),int(bool(enabled)),date.today().isoformat()))
        return {'club_id':int(club_id),'event_type':str(event_type).upper(),'enabled':bool(enabled),'persisted':True}

    def snooze(self, club_id: int, event_id: int, until: str) -> bool:
        with self.connection:
            cur=self.connection.execute('INSERT OR REPLACE INTO notification_snoozes(event_id,snoozed_until) SELECT event_id,? FROM club_events WHERE event_id=? AND club_id=?',(str(until),int(event_id),int(club_id)))
        return bool(cur.rowcount)

    def mark_all_read(self, club_id: int, event_type: str | None = None) -> int:
        query="UPDATE club_events SET status='READ' WHERE club_id=? AND status='OPEN'"; args=[int(club_id)]
        if event_type: query+=' AND type=?'; args.append(str(event_type).upper())
        with self.connection: cur=self.connection.execute(query,args)
        return int(cur.rowcount)

    def group_notifications(self, club_id: int) -> list[dict]:
        rows=self.connection.execute("SELECT type,COUNT(*) AS count,MAX(event_id) AS latest_event_id FROM club_events WHERE club_id=? GROUP BY type ORDER BY latest_event_id DESC",(int(club_id),)).fetchall()
        return [dict(row) for row in rows]

    def record_operational_failure(self, club_id: int, code: str, origin: str, description: str, reference: str) -> bool:
        return self.record(club_id,'FINANCEIRO','HIGH',f'Falha operacional: {code}',description,reference,origin=origin,impact=code)

    def archive(self, club_id: int, event_id: int) -> bool:
        with self.connection:
            cursor=self.connection.execute("UPDATE club_events SET status='ARCHIVED' WHERE club_id=? AND event_id=? AND status!='ARCHIVED'",(int(club_id),int(event_id)))
        return bool(cursor.rowcount)

    def group_by_day(self, club_id: int) -> list[dict]:
        rows=self.connection.execute("SELECT event_date,COUNT(*) AS count FROM club_events WHERE club_id=? AND type LIKE 'NOTICIA_%' GROUP BY event_date ORDER BY event_date DESC",(int(club_id),)).fetchall()
        return [dict(row) for row in rows]

    def mark_read(self, club_id: int, event_id: int) -> bool:
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE club_events SET status='READ' WHERE event_id=? AND club_id=? AND status='OPEN'",
                (event_id, club_id),
            )
        return bool(cursor.rowcount)
