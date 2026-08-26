from __future__ import annotations

from contextlib import nullcontext
from datetime import date
from pathlib import Path
import sqlite3


from engine.core.state_store import assert_mutable_state_path
EVENT_TYPES = frozenset({"TRANSFERENCIA", "LESAO", "CONTRATO", "PATROCINIO", "FINANCEIRO", "COMPETICAO", "ESTADIO", "TORCIDA"})
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

    def mark_read(self, club_id: int, event_id: int) -> bool:
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE club_events SET status='READ' WHERE event_id=? AND club_id=? AND status='OPEN'",
                (event_id, club_id),
            )
        return bool(cursor.rowcount)
