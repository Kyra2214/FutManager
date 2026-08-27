from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from engine.core.domain_errors import DomainError, DomainErrorCode

ITEM_IDS = tuple(range(2511, 2521))
ACTIONS = ("DEFINE_CONTRATO_DOMAIN110", "VALIDATE_RULES", "PERSIST_STATE", "EXPOSE_READ", "PROTECT_MUTATION", "AUDIT_FLOW", "OPTIMIZE_QUERY", "SIMULATE_SCENARIO", "DOCUMENT_CYCLE", "TEST_INTEGRATION")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_p2_contrato_domain110_registry(connection) -> None:
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS roadmap_p1_contrato_domain110_contrato_domain110s(
      item_id INTEGER PRIMARY KEY, domain_id INTEGER NOT NULL, contrato_domain110_name TEXT NOT NULL,
      payload_schema TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'CONSOLIDATED',
      source_of_truth TEXT NOT NULL DEFAULT 'SQL_GAMESTATE', contrato_domain110_json TEXT NOT NULL,
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS roadmap_p1_contrato_domain110s(
      contrato_domain110_key TEXT PRIMARY KEY, contrato_domain110_id INTEGER NOT NULL, club_id INTEGER,
      contrato_domain110_name TEXT NOT NULL, status TEXT NOT NULL, payload_json TEXT NOT NULL,
      payload_hash TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS roadmap_p1_contrato_domain110_audit(
      audit_id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
      action TEXT NOT NULL, allowed INTEGER NOT NULL, reason TEXT NOT NULL,
      payload TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(item_id, action)
    );
    CREATE INDEX IF NOT EXISTS idx_p1_contrato_domain110s_lookup ON roadmap_p1_contrato_domain110s(club_id, status, updated_at);
    """)
    now = _now()
    for item_id, action in zip(ITEM_IDS, ACTIONS, strict=True):
        contrato_domain110 = {"item_id": item_id, "domain_id": 8, "contrato_domain110_name": "contrato_domain110_state", "payload_schema": "contrato_domain110_key,contrato_domain110_id,club_id,contrato_domain110_name,status,payload", "action": action, "source_of_truth": "SQL_GAMESTATE", "schema_version": 1}
        connection.execute("INSERT OR IGNORE INTO roadmap_p1_contrato_domain110_contrato_domain110s VALUES(?,?,?,?,?,?,?,?,?)", (item_id, 8, "contrato_domain110_state", contrato_domain110["payload_schema"], "CONSOLIDATED", "SQL_GAMESTATE", json.dumps(contrato_domain110, sort_keys=True, separators=(",", ":")), now, now))
    connection.commit()


def validate_p1_contrato_domain110(connection, item_id: int) -> dict:
    row = connection.execute("SELECT * FROM roadmap_p1_contrato_domain110_contrato_domain110s WHERE item_id=?", (item_id,)).fetchone()
    if row is None:
        raise ValueError("P2_CONTRATO_DOMAIN110_NOT_FOUND")
    contrato_domain110 = json.loads(row["contrato_domain110_json"])
    checks = {"item_id": contrato_domain110.get("item_id") == item_id, "domain_id": contrato_domain110.get("domain_id") == 8, "contrato_domain110_name": contrato_domain110.get("contrato_domain110_name") == "contrato_domain110_state", "action": contrato_domain110.get("action") in ACTIONS, "source_of_truth": contrato_domain110.get("source_of_truth") == "SQL_GAMESTATE"}
    return {"status": "VALID" if all(checks.values()) else "INVALID", "item_id": item_id, "checks": checks, "contrato_domain110": contrato_domain110, "read_only": True}


def read_p1_contrato_domain110s(connection) -> list[dict]:
    return [{**dict(row), "contrato_domain110_json": json.loads(row["contrato_domain110_json"])} for row in connection.execute("SELECT * FROM roadmap_p1_contrato_domain110_contrato_domain110s ORDER BY item_id")]


def persist_p1_contrato_domain110(connection, key: str, contrato_domain110_id: int, contrato_domain110_name: str, payload: dict, club_id: int | None = None, status: str = "ACTIVE", actor: str = "") -> dict:
    if actor != "AUTHORIZED_SQL_SERVICE":
        raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    if not key.strip() or int(contrato_domain110_id) < 0 or (club_id is not None and int(club_id) < 0) or not contrato_domain110_name.strip() or status not in {"ACTIVE", "INACTIVE", "PENDING"} or not isinstance(payload, dict):
        raise ValueError("P2_CONTRATO_DOMAIN110_PAYLOAD_INVALID")
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    now = _now()
    connection.execute("INSERT INTO roadmap_p1_contrato_domain110s(contrato_domain110_key,contrato_domain110_id,club_id,contrato_domain110_name,status,payload_json,payload_hash,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(contrato_domain110_key) DO UPDATE SET contrato_domain110_id=excluded.contrato_domain110_id,club_id=excluded.club_id,contrato_domain110_name=excluded.contrato_domain110_name,status=excluded.status,payload_json=excluded.payload_json,payload_hash=excluded.payload_hash,updated_at=excluded.updated_at", (key.strip(), int(contrato_domain110_id), club_id, contrato_domain110_name.strip(), status, encoded, digest, now, now))
    connection.commit()
    row = connection.execute("SELECT * FROM roadmap_p1_contrato_domain110s WHERE contrato_domain110_key=?", (key.strip(),)).fetchone()
    return {**dict(row), "payload_json": json.loads(row["payload_json"])}


def read_p1_contrato_domain110_state(connection, key: str | None = None) -> list[dict]:
    contrato_domain110 = " WHERE contrato_domain110_key=?" if key else ""
    args = (key,) if key else ()
    return [{**dict(row), "payload_json": json.loads(row["payload_json"])} for row in connection.execute("SELECT * FROM roadmap_p1_contrato_domain110s" + contrato_domain110 + " ORDER BY updated_at DESC", args)]


def audit_p2_contrato_domain110s(connection) -> dict:
    rows = read_p1_contrato_domain110s(connection)
    invalid = [row["item_id"] for row in rows if validate_p1_contrato_domain110(connection, row["item_id"])["status"] != "VALID"]
    checks = {"count_10": len(rows) == 10, "expected_ids": {row["item_id"] for row in rows} == set(ITEM_IDS), "all_consolidated": all(row["status"] == "CONSOLIDATED" for row in rows), "sql_game_state": all(row["source_of_truth"] == "SQL_GAMESTATE" for row in rows), "valid_contrato_domain110s": not invalid}
    return {"status": "VALID" if all(checks.values()) else "INVALID", "contrato_domain110_count": len(rows), "state_count": connection.execute("SELECT COUNT(*) FROM roadmap_p1_contrato_domain110s").fetchone()[0], "checks": checks, "invalid_items": invalid, "read_only": True}


def protect_p1_contrato_domain110_mutation(connection, item_id: int, actor: str, payload: dict) -> dict:
    valid = validate_p1_contrato_domain110(connection, item_id)
    allowed = actor == "AUTHORIZED_SQL_SERVICE" and valid["status"] == "VALID"
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    connection.execute("INSERT OR REPLACE INTO roadmap_p1_contrato_domain110_audit(item_id,action,allowed,reason,payload,created_at) VALUES(?,?,?,?,?,?)", (item_id, "PROTECT_MUTATION", int(allowed), "ALLOWED" if allowed else "SQL_SERVICE_AUTHORIZATION_REQUIRED", encoded, _now()))
    connection.commit()
    if not allowed:
        raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    return {"allowed": True, "item_id": item_id, "payload_hash": hashlib.sha256(encoded.encode()).hexdigest()}


def audit_p2_contrato_domain110_flow(connection, item_id: int, action: str, allowed: bool, reason: str, payload: dict) -> dict:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    connection.execute("INSERT OR REPLACE INTO roadmap_p1_contrato_domain110_audit(item_id,action,allowed,reason,payload,created_at) VALUES(?,?,?,?,?,?)", (item_id, action, int(allowed), reason, encoded, _now()))
    connection.commit()
    return {"item_id": item_id, "action": action, "allowed": allowed, "reason": reason}
