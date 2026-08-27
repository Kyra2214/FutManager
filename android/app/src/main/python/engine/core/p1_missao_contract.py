"""Contrato P1 de missão baseado no ciclo canônico de SponsorshipService."""
from datetime import datetime, timezone
import hashlib
import json
import sqlite3

from engine.core.domain_errors import DomainError, DomainErrorCode
from engine.economy.sponsorships import FORMULA_VERSION, MISSION_TYPES

ITEM_IDS = tuple(range(3261, 3271))
ACTIONS = ("DEFINE_CONTRACT", "VALIDATE_RULES", "PERSIST_STATE", "EXPOSE_READ", "PROTECT_MUTATION", "AUDIT_FLOW", "OPTIMIZE_QUERY", "SIMULATE_SCENARIO", "DOCUMENT_CYCLE", "TEST_INTEGRATION")


def _now():
    return datetime.now(timezone.utc).isoformat()


def ensure_p1_missao_registry(connection: sqlite3.Connection) -> None:
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS roadmap_p1_missao_contracts(
      item_id INTEGER PRIMARY KEY, domain_id INTEGER NOT NULL, missao_name TEXT NOT NULL,
      payload_schema TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'CONSOLIDATED',
      source_of_truth TEXT NOT NULL DEFAULT 'SQL_GAMESTATE', formula_version TEXT NOT NULL,
      contract_json TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS roadmap_p1_missao_state(
      mission_type TEXT PRIMARY KEY, formula_version TEXT NOT NULL,
      payload_hash TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS roadmap_p1_missao_audit(
      audit_id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
      action TEXT NOT NULL, allowed INTEGER NOT NULL, reason TEXT NOT NULL,
      payload TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(item_id, action)
    );
    CREATE INDEX IF NOT EXISTS idx_p1_missao_type ON roadmap_p1_missao_state(mission_type);
    """)
    now = _now()
    for item_id, action in zip(ITEM_IDS, ACTIONS):
        contract = {"item_id": item_id, "domain_id": 24, "missao_name": "sponsor_mission", "action": action, "mission_types": MISSION_TYPES, "source_of_truth": "SQL_GAMESTATE", "formula_version": FORMULA_VERSION, "source_module": "engine.economy.sponsorships.SponsorshipService"}
        connection.execute("INSERT OR IGNORE INTO roadmap_p1_missao_contracts VALUES(?,?,?,?,?,?,?,?,?,?)", (item_id, 24, "sponsor_mission", "mission_type,title,target_value,current_value,reward,start_season,start_week,deadline_season,deadline_week,status", "CONSOLIDATED", "SQL_GAMESTATE", FORMULA_VERSION, json.dumps(contract, sort_keys=True, separators=(",", ":")), now, now))
    for mission_type in MISSION_TYPES:
        raw = json.dumps({"mission_type": mission_type, "formula_version": FORMULA_VERSION}, sort_keys=True, separators=(",", ":"))
        connection.execute("INSERT OR REPLACE INTO roadmap_p1_missao_state VALUES(?,?,?,?)", (mission_type, FORMULA_VERSION, hashlib.sha256(raw.encode()).hexdigest(), now))
    connection.commit()


def validate_p1_missao(connection, item_id: int) -> dict:
    row = connection.execute("SELECT * FROM roadmap_p1_missao_contracts WHERE item_id=?", (item_id,)).fetchone()
    if row is None:
        raise ValueError("P1_MISSAO_NOT_FOUND")
    contract = json.loads(row["contract_json"])
    checks = {"item_id": contract.get("item_id") == item_id, "domain_id": contract.get("domain_id") == 24, "mission_types": tuple(contract.get("mission_types", ())) == tuple(MISSION_TYPES), "formula_version": contract.get("formula_version") == FORMULA_VERSION, "source_of_truth": contract.get("source_of_truth") == "SQL_GAMESTATE", "source_module": contract.get("source_module") == "engine.economy.sponsorships.SponsorshipService"}
    return {"status": "VALID" if all(checks.values()) else "INVALID", "item_id": item_id, "checks": checks, "contract": contract, "read_only": True}


def read_p1_missoes(connection):
    return [{**dict(row), "contract_json": json.loads(row["contract_json"])} for row in connection.execute("SELECT * FROM roadmap_p1_missao_contracts ORDER BY item_id")]


def read_p1_missao_state(connection, mission_type=None):
    rows = connection.execute("SELECT * FROM roadmap_p1_missao_state" + (" WHERE mission_type=?" if mission_type else "") + " ORDER BY mission_type", ((mission_type,) if mission_type else ())).fetchall()
    return [dict(row) for row in rows]


def persist_p1_missao(connection, mission_type: str, payload: dict, actor: str = "") -> dict:
    if actor != "AUTHORIZED_SQL_SERVICE":
        raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    if mission_type not in MISSION_TYPES or not isinstance(payload, dict):
        raise ValueError("P1_MISSAO_PAYLOAD_INVALID")
    now = _now(); raw = json.dumps({"mission_type": mission_type, **payload, "formula_version": FORMULA_VERSION}, sort_keys=True, separators=(",", ":")); digest = hashlib.sha256(raw.encode()).hexdigest()
    connection.execute("UPDATE roadmap_p1_missao_state SET payload_hash=?,updated_at=? WHERE mission_type=?", (digest, now, mission_type)); connection.commit()
    return {"mission_type": mission_type, "formula_version": FORMULA_VERSION, "payload_hash": digest}


def audit_p1_missoes(connection):
    rows = read_p1_missoes(connection)
    checks = {"count_10": len(rows) == 10, "expected_ids": {row["item_id"] for row in rows} == set(ITEM_IDS), "all_consolidated": all(row["status"] == "CONSOLIDATED" for row in rows), "sql_game_state": all(row["source_of_truth"] == "SQL_GAMESTATE" for row in rows), "mission_types": all(tuple(row["contract_json"].get("mission_types", ())) == tuple(MISSION_TYPES) for row in rows), "formula_version": all(row["formula_version"] == FORMULA_VERSION for row in rows)}
    return {"status": "VALID" if all(checks.values()) else "INVALID", "mission_count": len(read_p1_missao_state(connection)), "checks": checks, "read_only": True}


def protect_p1_missao_mutation(connection, item_id: int, actor: str, payload: dict):
    valid = validate_p1_missao(connection, item_id); allowed = actor == "AUTHORIZED_SQL_SERVICE" and valid["status"] == "VALID"; encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    connection.execute("INSERT OR REPLACE INTO roadmap_p1_missao_audit(item_id,action,allowed,reason,payload,created_at) VALUES(?,?,?,?,?,?)", (item_id, "PROTECT_MUTATION", int(allowed), "ALLOWED" if allowed else "SQL_SERVICE_AUTHORIZATION_REQUIRED", encoded, _now())); connection.commit()
    if not allowed: raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    return {"allowed": True, "item_id": item_id, "payload_hash": hashlib.sha256(encoded.encode()).hexdigest()}
