from __future__ import annotations

import sqlite3
from datetime import date

SCHEMA = """
CREATE TABLE IF NOT EXISTS access_audit(audit_id INTEGER PRIMARY KEY AUTOINCREMENT,actor_id TEXT NOT NULL,action TEXT NOT NULL,target_id INTEGER,allowed INTEGER NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS safe_undo_commands(
  undo_id INTEGER PRIMARY KEY AUTOINCREMENT,
  command_type TEXT NOT NULL,
  target_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'AVAILABLE',
  created_at TEXT NOT NULL,
  undone_at TEXT
);
"""


class SafeUndoService:
    SAFE_COMMANDS = {"TRAINING_PLAN_CANCEL"}

    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def authorize(self, actor_id: str, action: str, target_id: int | None = None, confirmed: bool = False) -> dict:
        allowed=action in self.SAFE_COMMANDS and bool(confirmed)
        reason='ALLOWED' if allowed else ('CONFIRMATION_REQUIRED' if action in self.SAFE_COMMANDS else 'ACTION_NOT_WHITELISTED')
        with self.connection: self.connection.execute('INSERT INTO access_audit(actor_id,action,target_id,allowed,reason,created_at) VALUES(?,?,?,?,?,?)',(str(actor_id),action,target_id,int(allowed),reason,date.today().isoformat()))
        if not allowed: raise ValueError(reason)
        return {'actor_id':str(actor_id),'action':action,'target_id':target_id,'allowed':True,'reason':reason}

    def compliance_report(self) -> dict:
        rows=self.connection.execute('SELECT reason,COUNT(*) AS total FROM access_audit GROUP BY reason ORDER BY reason').fetchall()
        return {'access_events':[dict(r) for r in rows],'undo_commands':self.connection.execute('SELECT COUNT(*) FROM safe_undo_commands').fetchone()[0],'replays':self.connection.execute("SELECT COUNT(*) FROM safe_undo_commands WHERE status='UNDONE'").fetchone()[0],'source_of_truth':'GameState/SQLite','persisted':True}

    def register_training_plan(self, plan_id: int) -> dict:
        cursor = self.connection.execute(
            "INSERT INTO safe_undo_commands(command_type,target_id,created_at) VALUES(?,?,?)",
            ("TRAINING_PLAN_CANCEL", int(plan_id), date.today().isoformat()),
        )
        self.connection.commit()
        return {"undo_id": int(cursor.lastrowid), "command_type": "TRAINING_PLAN_CANCEL", "target_id": int(plan_id), "status": "AVAILABLE"}

    def undo(self, undo_id: int, actor_id: str = 'manager', confirmed: bool = True) -> dict:
        self.authorize(actor_id, 'TRAINING_PLAN_CANCEL', undo_id, confirmed)
        row = self.connection.execute("SELECT * FROM safe_undo_commands WHERE undo_id=?", (int(undo_id),)).fetchone()
        if row is None:
            raise KeyError(undo_id)
        if row['status'] == 'UNDONE':
            return {'undo_id': int(undo_id), 'status': 'UNDONE', 'idempotent': True}
        if row['command_type'] not in self.SAFE_COMMANDS:
            raise ValueError('SAFE_UNDO_NOT_ALLOWED')
        self.connection.execute("UPDATE safe_undo_commands SET status='UNDONE',undone_at=? WHERE undo_id=?", (date.today().isoformat(), int(undo_id)))
        self.connection.commit()
        return {'undo_id': int(undo_id), 'status': 'UNDONE', 'target_id': int(row['target_id']), 'idempotent': False}
