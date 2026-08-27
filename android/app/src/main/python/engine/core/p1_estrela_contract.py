"""Contrato P1 de estrela derivado das regras canônicas de patrocínio.

Fonte única: engine.economy.sponsorships.STAR_RULES e FORMULA_VERSION.
Este módulo não cria valores de gameplay; apenas registra, valida, lê e audita
as regras já usadas pelo SponsorshipService no GameState.
"""
from datetime import datetime, timezone
import hashlib
import json
import sqlite3

from engine.core.domain_errors import DomainError, DomainErrorCode
from engine.economy.sponsorships import FORMULA_VERSION, STAR_RULES

ITEM_IDS = tuple(range(3251, 3261))
ACTIONS = ("DEFINE_CONTRACT", "VALIDATE_RULES", "PERSIST_STATE", "EXPOSE_READ", "PROTECT_MUTATION", "AUDIT_FLOW", "OPTIMIZE_QUERY", "SIMULATE_SCENARIO", "DOCUMENT_CYCLE", "TEST_INTEGRATION")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_p1_estrela_registry(connection: sqlite3.Connection) -> None:
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS roadmap_p1_estrela_contracts(
      item_id INTEGER PRIMARY KEY, domain_id INTEGER NOT NULL,
      estrela_name TEXT NOT NULL, payload_schema TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'CONSOLIDATED', source_of_truth TEXT NOT NULL DEFAULT 'SQL_GAMESTATE',
      formula_version TEXT NOT NULL, contract_json TEXT NOT NULL,
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS roadmap_p1_estrela_state(
      star_rating INTEGER PRIMARY KEY, minimum_overall REAL NOT NULL,
      upfront_payment INTEGER NOT NULL, weekly_payment INTEGER NOT NULL,
      mission_bonus INTEGER NOT NULL, formula_version TEXT NOT NULL,
      payload_hash TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS roadmap_p1_estrela_audit(
      audit_id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
      action TEXT NOT NULL, allowed INTEGER NOT NULL, reason TEXT NOT NULL,
      payload TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(item_id, action)
    );
    CREATE INDEX IF NOT EXISTS idx_p1_estrela_state_overall ON roadmap_p1_estrela_state(minimum_overall, star_rating);
    """)
    now = _now()
    for item_id, action in zip(ITEM_IDS, ACTIONS):
        payload = {"item_id": item_id, "domain_id": 24, "estrela_name": "sponsor_star_rating", "action": action, "source_of_truth": "SQL_GAMESTATE", "formula_version": FORMULA_VERSION, "source_module": "engine.economy.sponsorships.STAR_RULES"}
        connection.execute("INSERT OR IGNORE INTO roadmap_p1_estrela_contracts VALUES(?,?,?,?,?,?,?,?,?,?)", (item_id, 24, "sponsor_star_rating", "star_rating,minimum_overall,upfront_payment,weekly_payment,mission_bonus", "CONSOLIDATED", "SQL_GAMESTATE", FORMULA_VERSION, json.dumps(payload, sort_keys=True, separators=(",", ":")), now, now))
    for rating, rule in STAR_RULES.items():
        payload = json.dumps({"star_rating": rating, **rule, "formula_version": FORMULA_VERSION}, sort_keys=True, separators=(",", ":"))
        connection.execute("INSERT OR REPLACE INTO roadmap_p1_estrela_state VALUES(?,?,?,?,?,?,?,?)", (rating, rule["minimum_overall"], rule["upfront"], rule["weekly"], rule["mission"], FORMULA_VERSION, hashlib.sha256(payload.encode()).hexdigest(), now))
    connection.commit()


def validate_p1_estrela(connection: sqlite3.Connection, item_id: int) -> dict:
    row = connection.execute("SELECT * FROM roadmap_p1_estrela_contracts WHERE item_id=?", (item_id,)).fetchone()
    if row is None:
        raise ValueError("P1_ESTRELA_NOT_FOUND")
    contract = json.loads(row["contract_json"])
    checks = {"item_id": contract.get("item_id") == item_id, "domain_id": contract.get("domain_id") == 24, "formula_version": contract.get("formula_version") == FORMULA_VERSION, "source_of_truth": contract.get("source_of_truth") == "SQL_GAMESTATE", "source_module": contract.get("source_module") == "engine.economy.sponsorships.STAR_RULES"}
    return {"status": "VALID" if all(checks.values()) else "INVALID", "item_id": item_id, "checks": checks, "contract": contract, "read_only": True}


def read_p1_estrelas(connection) -> list[dict]:
    return [{**dict(row), "contract_json": json.loads(row["contract_json"])} for row in connection.execute("SELECT * FROM roadmap_p1_estrela_contracts ORDER BY item_id")]


def read_p1_estrela_state(connection, star_rating: int | None = None) -> list[dict]:
    rows = connection.execute("SELECT * FROM roadmap_p1_estrela_state" + (" WHERE star_rating=?" if star_rating is not None else "") + " ORDER BY star_rating", ((star_rating,) if star_rating is not None else ())).fetchall()
    return [dict(row) for row in rows]


def persist_p1_estrela(connection, star_rating: int, payload: dict, actor: str = "") -> dict:
    if actor != "AUTHORIZED_SQL_SERVICE":
        raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    if int(star_rating) not in STAR_RULES or not isinstance(payload, dict):
        raise ValueError("P1_ESTRELA_PAYLOAD_INVALID")
    rule = STAR_RULES[int(star_rating)]
    now = _now()
    raw = json.dumps({"star_rating": int(star_rating), **rule, **payload, "formula_version": FORMULA_VERSION}, sort_keys=True, separators=(",", ":"))
    connection.execute("UPDATE roadmap_p1_estrela_state SET payload_hash=?,updated_at=? WHERE star_rating=?", (hashlib.sha256(raw.encode()).hexdigest(), now, int(star_rating)))
    connection.commit()
    return {"star_rating": int(star_rating), **rule, "formula_version": FORMULA_VERSION, "payload_hash": hashlib.sha256(raw.encode()).hexdigest()}


def audit_p1_estrelas(connection) -> dict:
    rows = read_p1_estrelas(connection)
    checks = {"count_10": len(rows) == 10, "expected_ids": {row["item_id"] for row in rows} == set(ITEM_IDS), "all_consolidated": all(row["status"] == "CONSOLIDATED" for row in rows), "sql_game_state": all(row["source_of_truth"] == "SQL_GAMESTATE" for row in rows), "formula_version": all(row["formula_version"] == FORMULA_VERSION for row in rows), "source_module": all(row["contract_json"].get("source_module") == "engine.economy.sponsorships.STAR_RULES" for row in rows)}
    return {"status": "VALID" if all(checks.values()) else "INVALID", "star_count": len(read_p1_estrela_state(connection)), "checks": checks, "read_only": True}


def protect_p1_estrela_mutation(connection, item_id: int, actor: str, payload: dict) -> dict:
    valid = validate_p1_estrela(connection, item_id)
    allowed = actor == "AUTHORIZED_SQL_SERVICE" and valid["status"] == "VALID"
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    connection.execute("INSERT OR REPLACE INTO roadmap_p1_estrela_audit(item_id,action,allowed,reason,payload,created_at) VALUES(?,?,?,?,?,?)", (item_id, "PROTECT_MUTATION", int(allowed), "ALLOWED" if allowed else "SQL_SERVICE_AUTHORIZATION_REQUIRED", encoded, _now()))
    connection.commit()
    if not allowed:
        raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    return {"allowed": True, "item_id": item_id, "payload_hash": hashlib.sha256(encoded.encode()).hexdigest()}
