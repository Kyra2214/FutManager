from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from engine.core.domain_errors import DomainError, DomainErrorCode

ITEM_IDS = tuple(range(1061, 1071))
ACTIONS = ('DEFINE_CONTRACT', 'VALIDATE_RULES', 'PERSIST_STATE', 'EXPOSE_READ', 'PROTECT_MUTATION', 'AUDIT_FLOW', 'OPTIMIZE_QUERY', 'SIMULATE_SCENARIO', 'DOCUMENT_CYCLE', 'TEST_INTEGRATION')
ERROR_CODES = tuple(code.value for code in DomainErrorCode)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_p1_error_registry(connection: sqlite3.Connection) -> None:
    connection.executescript('''
    CREATE TABLE IF NOT EXISTS roadmap_p1_errors(
      item_id INTEGER PRIMARY KEY, domain_id INTEGER NOT NULL, error_code TEXT NOT NULL,
      action TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'CONSOLIDATED',
      source_of_truth TEXT NOT NULL DEFAULT 'SQL_GAMESTATE', contract_json TEXT NOT NULL,
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS roadmap_p1_error_audit(
      audit_id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL, action TEXT NOT NULL,
      allowed INTEGER NOT NULL, reason TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL,
      UNIQUE(item_id, action)
    );
    CREATE INDEX IF NOT EXISTS idx_roadmap_p1_error_lookup ON roadmap_p1_errors(error_code, action, status);
    CREATE INDEX IF NOT EXISTS idx_roadmap_p1_error_audit_item ON roadmap_p1_error_audit(item_id, audit_id);
    ''')
    now = _now()
    for item_id, action in zip(ITEM_IDS, ACTIONS):
        error_code = ERROR_CODES[(item_id - 1061) % len(ERROR_CODES)]
        contract = {'item_id': item_id, 'domain_id': 2, 'error_code': error_code, 'action': action, 'source_of_truth': 'SQL_GAMESTATE', 'schema_version': 1}
        connection.execute('INSERT OR IGNORE INTO roadmap_p1_errors(item_id,domain_id,error_code,action,status,source_of_truth,contract_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)', (item_id, 2, error_code, action, 'CONSOLIDATED', 'SQL_GAMESTATE', json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(',', ':')), now, now))
    connection.commit()


def validate_p1_error(connection: sqlite3.Connection, item_id: int) -> dict[str, Any]:
    row = connection.execute('SELECT * FROM roadmap_p1_errors WHERE item_id=?', (item_id,)).fetchone()
    if row is None: raise ValueError('P1_ERROR_NOT_FOUND')
    contract = json.loads(row['contract_json'])
    checks = {'item_id': int(contract.get('item_id')) == int(item_id), 'domain_id': int(contract.get('domain_id')) == 2, 'error_code': contract.get('error_code') in ERROR_CODES, 'action': contract.get('action') in ACTIONS, 'source_of_truth': contract.get('source_of_truth') == 'SQL_GAMESTATE', 'schema_version': contract.get('schema_version') == 1}
    return {'status': 'VALID' if all(checks.values()) else 'INVALID', 'item_id': item_id, 'checks': checks, 'contract': contract, 'read_only': True}


def read_p1_errors(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    return [{**dict(row), 'contract_json': json.loads(row['contract_json'])} for row in connection.execute('SELECT * FROM roadmap_p1_errors ORDER BY item_id').fetchall()]


def protect_p1_error_mutation(connection: sqlite3.Connection, item_id: int, actor: str, payload: dict[str, Any]) -> dict[str, Any]:
    validation = validate_p1_error(connection, item_id)
    allowed = bool(actor == 'AUTHORIZED_SQL_SERVICE' and validation['status'] == 'VALID')
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    connection.execute('INSERT OR REPLACE INTO roadmap_p1_error_audit(item_id,action,allowed,reason,payload,created_at) VALUES(?,?,?,?,?,?)', (item_id, 'PROTECT_MUTATION', int(allowed), 'ALLOWED' if allowed else 'SQL_SERVICE_AUTHORIZATION_REQUIRED', serialized, _now()))
    connection.commit()
    if not allowed: raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    return {'allowed': True, 'item_id': item_id, 'payload_hash': hashlib.sha256(serialized.encode()).hexdigest()}


def audit_p1_errors(connection: sqlite3.Connection) -> dict[str, Any]:
    rows = connection.execute('SELECT item_id,domain_id,error_code,action,status,source_of_truth,contract_json FROM roadmap_p1_errors ORDER BY item_id').fetchall()
    invalid = []
    for row in rows:
        try:
            contract = json.loads(row['contract_json'])
            if not (int(contract.get('item_id')) == int(row['item_id']) and int(contract.get('domain_id')) == 2 and contract.get('error_code') in ERROR_CODES and contract.get('action') in ACTIONS and contract.get('source_of_truth') == 'SQL_GAMESTATE' and contract.get('schema_version') == 1): invalid.append(int(row['item_id']))
        except (TypeError, ValueError, json.JSONDecodeError): invalid.append(int(row['item_id']))
    checks = {'count_10': len(rows) == 10, 'expected_ids': {int(row['item_id']) for row in rows} == set(ITEM_IDS), 'all_consolidated': all(row['status'] == 'CONSOLIDATED' for row in rows), 'sql_game_state': all(row['source_of_truth'] == 'SQL_GAMESTATE' for row in rows), 'valid_contracts': not invalid}
    return {'status': 'VALID' if all(checks.values()) else 'INVALID', 'error_count': len(rows), 'checks': checks, 'invalid_items': invalid, 'read_only': True}
