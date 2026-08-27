from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone

from engine.core.domain_errors import DomainError, DomainErrorCode

ITEM_IDS = tuple(range(1111, 1121))
ACTIONS = (
    "DEFINE_CONTRACT", "VALIDATE_RULES", "PERSIST_STATE", "EXPOSE_READ", "PROTECT_MUTATION",
    "AUDIT_FLOW", "OPTIMIZE_QUERY", "SIMULATE_SCENARIO", "DOCUMENT_CYCLE", "TEST_INTEGRATION",
)
MAX_EVENTS = 500


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_p1_telemetry_registry(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS roadmap_p1_telemetry_contracts(
          item_id INTEGER PRIMARY KEY, domain_id INTEGER NOT NULL,
          event_name TEXT NOT NULL, payload_schema TEXT NOT NULL,
          retention_days INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'CONSOLIDATED',
          source_of_truth TEXT NOT NULL DEFAULT 'SQL_GAMESTATE', contract_json TEXT NOT NULL,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS roadmap_p1_telemetry_events(
          event_id INTEGER PRIMARY KEY AUTOINCREMENT, event_key TEXT NOT NULL UNIQUE,
          event_name TEXT NOT NULL, career_id INTEGER, season_number INTEGER,
          week_number INTEGER, payload_json TEXT NOT NULL, payload_hash TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS roadmap_p1_telemetry_audit(
          audit_id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
          action TEXT NOT NULL, allowed INTEGER NOT NULL, reason TEXT NOT NULL,
          payload TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(item_id, action)
        );
        CREATE INDEX IF NOT EXISTS idx_p1_telemetry_events_lookup ON roadmap_p1_telemetry_events(event_name, career_id, season_number, week_number);
        """
    )
    now = _now()
    for item_id, action in zip(ITEM_IDS, ACTIONS):
        contract = {
            "item_id": item_id, "domain_id": 2, "event_name": "career.telemetry",
            "payload_schema": "event_key,event_name,career_id,season_number,week_number,payload",
            "retention_days": 365, "action": action, "source_of_truth": "SQL_GAMESTATE", "schema_version": 1,
        }
        connection.execute(
            "INSERT OR IGNORE INTO roadmap_p1_telemetry_contracts VALUES(?,?,?,?,?,?,?,?,?,?)",
            (item_id, 2, "career.telemetry", contract["payload_schema"], 365, "CONSOLIDATED", "SQL_GAMESTATE", json.dumps(contract, sort_keys=True, separators=(",", ":")), now, now),
        )
    connection.commit()


def validate_p1_telemetry(connection: sqlite3.Connection, item_id: int) -> dict:
    row = connection.execute("SELECT * FROM roadmap_p1_telemetry_contracts WHERE item_id=?", (item_id,)).fetchone()
    if row is None:
        raise ValueError("P1_TELEMETRY_NOT_FOUND")
    contract = json.loads(row["contract_json"])
    checks = {
        "item_id": contract.get("item_id") == item_id,
        "domain_id": contract.get("domain_id") == 2,
        "event_name": contract.get("event_name") == "career.telemetry",
        "retention_days": isinstance(contract.get("retention_days"), int) and contract.get("retention_days") > 0,
        "action": contract.get("action") in ACTIONS,
        "source_of_truth": contract.get("source_of_truth") == "SQL_GAMESTATE",
    }
    return {"status": "VALID" if all(checks.values()) else "INVALID", "item_id": item_id, "checks": checks, "contract": contract, "read_only": True}


def read_p1_telemetry_contracts(connection: sqlite3.Connection) -> list[dict]:
    return [{**dict(row), "contract_json": json.loads(row["contract_json"])} for row in connection.execute("SELECT * FROM roadmap_p1_telemetry_contracts ORDER BY item_id")]


def record_p1_telemetry_event(connection: sqlite3.Connection, event_key: str, event_name: str, payload: dict, career_id: int | None = None, season_number: int | None = None, week_number: int | None = None, actor: str = "") -> dict:
    if actor != "AUTHORIZED_SQL_SERVICE":
        raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    if not event_key.strip() or not event_name.strip() or not isinstance(payload, dict):
        raise ValueError("P1_TELEMETRY_PAYLOAD_INVALID")
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()
    connection.execute("INSERT OR IGNORE INTO roadmap_p1_telemetry_events(event_key,event_name,career_id,season_number,week_number,payload_json,payload_hash,created_at) VALUES(?,?,?,?,?,?,?,?)", (event_key.strip(), event_name.strip(), career_id, season_number, week_number, payload_json, payload_hash, _now()))
    connection.commit()
    row = connection.execute("SELECT * FROM roadmap_p1_telemetry_events WHERE event_key=?", (event_key.strip(),)).fetchone()
    return {**dict(row), "payload_json": json.loads(row["payload_json"]), "idempotent": row["payload_hash"] == payload_hash}


def read_p1_telemetry_events(connection: sqlite3.Connection, career_id: int | None = None, limit: int = 100) -> list[dict]:
    limit = max(1, min(int(limit), MAX_EVENTS))
    if career_id is None:
        rows = connection.execute("SELECT * FROM roadmap_p1_telemetry_events ORDER BY event_id DESC LIMIT ?", (limit,)).fetchall()
    else:
        rows = connection.execute("SELECT * FROM roadmap_p1_telemetry_events WHERE career_id=? ORDER BY event_id DESC LIMIT ?", (career_id, limit)).fetchall()
    return [{**dict(row), "payload_json": json.loads(row["payload_json"])} for row in rows]


def audit_p1_telemetry(connection: sqlite3.Connection) -> dict:
    contracts = read_p1_telemetry_contracts(connection)
    invalid = [item["item_id"] for item in contracts if validate_p1_telemetry(connection, item["item_id"])["status"] != "VALID"]
    duplicate_keys = connection.execute("SELECT COUNT(*) - COUNT(DISTINCT event_key) FROM roadmap_p1_telemetry_events").fetchone()[0]
    checks = {"count_10": len(contracts) == 10, "expected_ids": {x["item_id"] for x in contracts} == set(ITEM_IDS), "all_consolidated": all(x["status"] == "CONSOLIDATED" for x in contracts), "sql_game_state": all(x["source_of_truth"] == "SQL_GAMESTATE" for x in contracts), "valid_contracts": not invalid, "unique_event_keys": duplicate_keys == 0}
    return {"status": "VALID" if all(checks.values()) else "INVALID", "telemetry_count": len(contracts), "event_count": connection.execute("SELECT COUNT(*) FROM roadmap_p1_telemetry_events").fetchone()[0], "checks": checks, "invalid_items": invalid, "read_only": True}


def protect_p1_telemetry_mutation(connection: sqlite3.Connection, item_id: int, actor: str, payload: dict) -> dict:
    validation = validate_p1_telemetry(connection, item_id)
    allowed = actor == "AUTHORIZED_SQL_SERVICE" and validation["status"] == "VALID"
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    connection.execute("INSERT OR REPLACE INTO roadmap_p1_telemetry_audit(item_id,action,allowed,reason,payload,created_at) VALUES(?,?,?,?,?,?)", (item_id, "PROTECT_MUTATION", int(allowed), "ALLOWED" if allowed else "SQL_SERVICE_AUTHORIZATION_REQUIRED", payload_json, _now()))
    connection.commit()
    if not allowed:
        raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    return {"allowed": True, "item_id": item_id, "payload_hash": hashlib.sha256(payload_json.encode()).hexdigest()}
