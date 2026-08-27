from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone

from engine.core.domain_errors import DomainError, DomainErrorCode

ITEM_IDS = tuple(range(1151, 1161))
ACTIONS = ("DEFINE_CONTRACT", "VALIDATE_RULES", "PERSIST_STATE", "EXPOSE_READ", "PROTECT_MUTATION", "AUDIT_FLOW", "OPTIMIZE_QUERY", "SIMULATE_SCENARIO", "DOCUMENT_CYCLE", "TEST_INTEGRATION")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_p1_session_registry(connection: sqlite3.Connection) -> None:
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS roadmap_p1_session_contracts(item_id INTEGER PRIMARY KEY, domain_id INTEGER NOT NULL, session_name TEXT NOT NULL, payload_schema TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'CONSOLIDATED', source_of_truth TEXT NOT NULL DEFAULT 'SQL_GAMESTATE', contract_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS roadmap_p1_sessions(session_key TEXT PRIMARY KEY, manager_id INTEGER, career_id INTEGER, status TEXT NOT NULL, payload_json TEXT NOT NULL, payload_hash TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS roadmap_p1_session_audit(audit_id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL, action TEXT NOT NULL, allowed INTEGER NOT NULL, reason TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(item_id, action));
    CREATE INDEX IF NOT EXISTS idx_p1_sessions_lookup ON roadmap_p1_sessions(career_id, manager_id, status, updated_at);
    """)
    now = _now()
    for item_id, action in zip(ITEM_IDS, ACTIONS):
        contract = {"item_id": item_id, "domain_id": 3, "session_name": "manager_session", "payload_schema": "session_key,manager_id,career_id,status,payload", "action": action, "source_of_truth": "SQL_GAMESTATE", "schema_version": 1}
        connection.execute("INSERT OR IGNORE INTO roadmap_p1_session_contracts VALUES(?,?,?,?,?,?,?,?,?)", (item_id, 3, "manager_session", contract["payload_schema"], "CONSOLIDATED", "SQL_GAMESTATE", json.dumps(contract, sort_keys=True, separators=(",", ":")), now, now))
    connection.commit()


def validate_p1_session(connection: sqlite3.Connection, item_id: int) -> dict:
    row = connection.execute("SELECT * FROM roadmap_p1_session_contracts WHERE item_id=?", (item_id,)).fetchone()
    if row is None: raise ValueError("P1_SESSION_NOT_FOUND")
    contract = json.loads(row["contract_json"])
    checks = {"item_id": contract.get("item_id") == item_id, "domain_id": contract.get("domain_id") == 3, "session_name": contract.get("session_name") == "manager_session", "action": contract.get("action") in ACTIONS, "source_of_truth": contract.get("source_of_truth") == "SQL_GAMESTATE"}
    return {"status": "VALID" if all(checks.values()) else "INVALID", "item_id": item_id, "checks": checks, "contract": contract, "read_only": True}


def read_p1_sessions(connection: sqlite3.Connection) -> list[dict]:
    return [{**dict(row), "contract_json": json.loads(row["contract_json"])} for row in connection.execute("SELECT * FROM roadmap_p1_session_contracts ORDER BY item_id")]


def persist_p1_session(connection: sqlite3.Connection, session_key: str, status: str, payload: dict, manager_id: int | None = None, career_id: int | None = None, actor: str = "") -> dict:
    if actor != "AUTHORIZED_SQL_SERVICE": raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    if not session_key.strip() or status not in {"ACTIVE", "EXPIRED", "REVOKED"} or not isinstance(payload, dict): raise ValueError("P1_SESSION_PAYLOAD_INVALID")
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")); digest = hashlib.sha256(encoded.encode()).hexdigest(); now = _now()
    connection.execute("INSERT INTO roadmap_p1_sessions(session_key,manager_id,career_id,status,payload_json,payload_hash,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(session_key) DO UPDATE SET status=excluded.status,payload_json=excluded.payload_json,payload_hash=excluded.payload_hash,updated_at=excluded.updated_at", (session_key.strip(), manager_id, career_id, status, encoded, digest, now, now)); connection.commit()
    row = connection.execute("SELECT * FROM roadmap_p1_sessions WHERE session_key=?", (session_key.strip(),)).fetchone(); return {**dict(row), "payload_json": json.loads(row["payload_json"]), "payload_hash": digest}


def read_p1_session_state(connection: sqlite3.Connection, session_key: str | None = None) -> list[dict]:
    sql = "SELECT * FROM roadmap_p1_sessions ORDER BY updated_at DESC"; args: tuple = ()
    if session_key: sql = "SELECT * FROM roadmap_p1_sessions WHERE session_key=?"; args = (session_key,)
    return [{**dict(row), "payload_json": json.loads(row["payload_json"])} for row in connection.execute(sql, args).fetchall()]


def audit_p1_sessions(connection: sqlite3.Connection) -> dict:
    contracts = read_p1_sessions(connection); invalid = [x["item_id"] for x in contracts if validate_p1_session(connection, x["item_id"])["status"] != "VALID"]; checks = {"count_10": len(contracts) == 10, "expected_ids": {x["item_id"] for x in contracts} == set(ITEM_IDS), "all_consolidated": all(x["status"] == "CONSOLIDATED" for x in contracts), "sql_game_state": all(x["source_of_truth"] == "SQL_GAMESTATE" for x in contracts), "valid_contracts": not invalid}
    return {"status": "VALID" if all(checks.values()) else "INVALID", "session_count": len(contracts), "state_count": connection.execute("SELECT COUNT(*) FROM roadmap_p1_sessions").fetchone()[0], "checks": checks, "invalid_items": invalid, "read_only": True}


def protect_p1_session_mutation(connection: sqlite3.Connection, item_id: int, actor: str, payload: dict) -> dict:
    validation = validate_p1_session(connection, item_id); allowed = actor == "AUTHORIZED_SQL_SERVICE" and validation["status"] == "VALID"; encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")); connection.execute("INSERT OR REPLACE INTO roadmap_p1_session_audit(item_id,action,allowed,reason,payload,created_at) VALUES(?,?,?,?,?,?)", (item_id, "PROTECT_MUTATION", int(allowed), "ALLOWED" if allowed else "SQL_SERVICE_AUTHORIZATION_REQUIRED", encoded, _now())); connection.commit()
    if not allowed: raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    return {"allowed": True, "item_id": item_id, "payload_hash": hashlib.sha256(encoded.encode()).hexdigest()}
