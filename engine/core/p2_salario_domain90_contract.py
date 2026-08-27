from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from engine.core.domain_errors import DomainError, DomainErrorCode

ITEM_IDS = tuple(range(3171, 3181))
ACTIONS = ("DEFINE_SALARIO_DOMAIN90", "VALIDATE_RULES", "PERSIST_STATE", "EXPOSE_READ", "PROTECT_MUTATION", "AUDIT_FLOW", "OPTIMIZE_QUERY", "SIMULATE_SCENARIO", "DOCUMENT_CYCLE", "TEST_INTEGRATION")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_p2_salario_domain90_registry(connection) -> None:
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS roadmap_p1_salario_domain90_salario_domain90s(
      item_id INTEGER PRIMARY KEY, domain_id INTEGER NOT NULL, salario_domain90_name TEXT NOT NULL,
      payload_schema TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'CONSOLIDATED',
      source_of_truth TEXT NOT NULL DEFAULT 'SQL_GAMESTATE', salario_domain90_json TEXT NOT NULL,
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS roadmap_p1_salario_domain90s(
      salario_domain90_key TEXT PRIMARY KEY, salario_domain90_id INTEGER NOT NULL, club_id INTEGER,
      salario_domain90_name TEXT NOT NULL, status TEXT NOT NULL, payload_json TEXT NOT NULL,
      payload_hash TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS roadmap_p1_salario_domain90_audit(
      audit_id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
      action TEXT NOT NULL, allowed INTEGER NOT NULL, reason TEXT NOT NULL,
      payload TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(item_id, action)
    );
    CREATE INDEX IF NOT EXISTS idx_p1_salario_domain90s_lookup ON roadmap_p1_salario_domain90s(club_id, status, updated_at);
    """)
    now = _now()
    for item_id, action in zip(ITEM_IDS, ACTIONS, strict=True):
        salario_domain90 = {"item_id": item_id, "domain_id": 8, "salario_domain90_name": "salario_domain90_state", "payload_schema": "salario_domain90_key,salario_domain90_id,club_id,salario_domain90_name,status,payload", "action": action, "source_of_truth": "SQL_GAMESTATE", "schema_version": 1}
        connection.execute("INSERT OR IGNORE INTO roadmap_p1_salario_domain90_salario_domain90s VALUES(?,?,?,?,?,?,?,?,?)", (item_id, 8, "salario_domain90_state", salario_domain90["payload_schema"], "CONSOLIDATED", "SQL_GAMESTATE", json.dumps(salario_domain90, sort_keys=True, separators=(",", ":")), now, now))
    connection.commit()


def validate_p1_salario_domain90(connection, item_id: int) -> dict:
    row = connection.execute("SELECT * FROM roadmap_p1_salario_domain90_salario_domain90s WHERE item_id=?", (item_id,)).fetchone()
    if row is None:
        raise ValueError("P2_SALARIO_DOMAIN90_NOT_FOUND")
    salario_domain90 = json.loads(row["salario_domain90_json"])
    checks = {"item_id": salario_domain90.get("item_id") == item_id, "domain_id": salario_domain90.get("domain_id") == 8, "salario_domain90_name": salario_domain90.get("salario_domain90_name") == "salario_domain90_state", "action": salario_domain90.get("action") in ACTIONS, "source_of_truth": salario_domain90.get("source_of_truth") == "SQL_GAMESTATE"}
    return {"status": "VALID" if all(checks.values()) else "INVALID", "item_id": item_id, "checks": checks, "salario_domain90": salario_domain90, "read_only": True}


def read_p1_salario_domain90s(connection) -> list[dict]:
    return [{**dict(row), "salario_domain90_json": json.loads(row["salario_domain90_json"])} for row in connection.execute("SELECT * FROM roadmap_p1_salario_domain90_salario_domain90s ORDER BY item_id")]


def persist_p1_salario_domain90(connection, key: str, salario_domain90_id: int, salario_domain90_name: str, payload: dict, club_id: int | None = None, status: str = "ACTIVE", actor: str = "") -> dict:
    if actor != "AUTHORIZED_SQL_SERVICE":
        raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    if not key.strip() or int(salario_domain90_id) < 0 or (club_id is not None and int(club_id) < 0) or not salario_domain90_name.strip() or status not in {"ACTIVE", "INACTIVE", "PENDING"} or not isinstance(payload, dict):
        raise ValueError("P2_SALARIO_DOMAIN90_PAYLOAD_INVALID")
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    now = _now()
    connection.execute("INSERT INTO roadmap_p1_salario_domain90s(salario_domain90_key,salario_domain90_id,club_id,salario_domain90_name,status,payload_json,payload_hash,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(salario_domain90_key) DO UPDATE SET salario_domain90_id=excluded.salario_domain90_id,club_id=excluded.club_id,salario_domain90_name=excluded.salario_domain90_name,status=excluded.status,payload_json=excluded.payload_json,payload_hash=excluded.payload_hash,updated_at=excluded.updated_at", (key.strip(), int(salario_domain90_id), club_id, salario_domain90_name.strip(), status, encoded, digest, now, now))
    connection.commit()
    row = connection.execute("SELECT * FROM roadmap_p1_salario_domain90s WHERE salario_domain90_key=?", (key.strip(),)).fetchone()
    return {**dict(row), "payload_json": json.loads(row["payload_json"])}


def read_p1_salario_domain90_state(connection, key: str | None = None) -> list[dict]:
    salario_domain90 = " WHERE salario_domain90_key=?" if key else ""
    args = (key,) if key else ()
    return [{**dict(row), "payload_json": json.loads(row["payload_json"])} for row in connection.execute("SELECT * FROM roadmap_p1_salario_domain90s" + salario_domain90 + " ORDER BY updated_at DESC", args)]


def audit_p2_salario_domain90s(connection) -> dict:
    rows = read_p1_salario_domain90s(connection)
    invalid = [row["item_id"] for row in rows if validate_p1_salario_domain90(connection, row["item_id"])["status"] != "VALID"]
    checks = {"count_10": len(rows) == 10, "expected_ids": {row["item_id"] for row in rows} == set(ITEM_IDS), "all_consolidated": all(row["status"] == "CONSOLIDATED" for row in rows), "sql_game_state": all(row["source_of_truth"] == "SQL_GAMESTATE" for row in rows), "valid_salario_domain90s": not invalid}
    return {"status": "VALID" if all(checks.values()) else "INVALID", "salario_domain90_count": len(rows), "state_count": connection.execute("SELECT COUNT(*) FROM roadmap_p1_salario_domain90s").fetchone()[0], "checks": checks, "invalid_items": invalid, "read_only": True}


def protect_p1_salario_domain90_mutation(connection, item_id: int, actor: str, payload: dict) -> dict:
    valid = validate_p1_salario_domain90(connection, item_id)
    allowed = actor == "AUTHORIZED_SQL_SERVICE" and valid["status"] == "VALID"
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    connection.execute("INSERT OR REPLACE INTO roadmap_p1_salario_domain90_audit(item_id,action,allowed,reason,payload,created_at) VALUES(?,?,?,?,?,?)", (item_id, "PROTECT_MUTATION", int(allowed), "ALLOWED" if allowed else "SQL_SERVICE_AUTHORIZATION_REQUIRED", encoded, _now()))
    connection.commit()
    if not allowed:
        raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    return {"allowed": True, "item_id": item_id, "payload_hash": hashlib.sha256(encoded.encode()).hexdigest()}


def audit_p2_salario_domain90_flow(connection, item_id: int, action: str, allowed: bool, reason: str, payload: dict) -> dict:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    connection.execute("INSERT OR REPLACE INTO roadmap_p1_salario_domain90_audit(item_id,action,allowed,reason,payload,created_at) VALUES(?,?,?,?,?,?)", (item_id, action, int(allowed), reason, encoded, _now()))
    connection.commit()
    return {"item_id": item_id, "action": action, "allowed": allowed, "reason": reason}
