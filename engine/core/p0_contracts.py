from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from engine.core.domain_errors import DomainError, DomainErrorCode


P0_SCHEMA_VERSION = 1
P0_DOMAINS = {
    1: 'Fundação e persistência do GameState',
    2: 'Gateway e contratos',
    3: 'Autenticação e governança de acesso',
    4: 'Catálogo de clubes',
    5: 'Catálogo de jogadores',
    6: 'Seleções nacionais',
    7: 'Ligas nacionais',
    8: 'Liga paralela da carreira',
    9: 'Competições continentais',
    10: 'Calendário mundial',
    11: 'Motor de partidas',
    12: 'Estatísticas avançadas',
    13: 'IA dos clubes',
    14: 'Elenco e hierarquia',
    15: 'Contratos de jogadores',
    16: 'Comissão técnica',
    17: 'Centro de treinamento',
    18: 'Base e formação',
    19: 'Saúde e lesões',
    20: 'Treinamento e evolução',
    21: 'Mercado e transferências',
    22: 'Scouting e observação',
    23: 'Finanças e contabilidade',
    24: 'Patrocínios e comercial',
    25: 'Estádio e torcida',
    26: 'Viagens e logística',
    27: 'Simulação mundial',
    28: 'Notícias e eventos',
    29: 'Manager e carreira',
    30: 'Interface, testes e entrega',
}
P0_ACTIONS = ('DEFINE_CONTRACT', 'VALIDATE_RULES', 'PERSIST_STATE', 'EXPOSE_READ', 'PROTECT_MUTATION', 'AUDIT_FLOW', 'OPTIMIZE_QUERY', 'SIMULATE_SCENARIO', 'DOCUMENT_CYCLE', 'TEST_INTEGRATION')


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _action_for_item(item_id: int) -> str:
    return P0_ACTIONS[(item_id % 100) - 41]


def _domain_for_item(item_id: int) -> int:
    return (item_id - 941) // 100 + 1


def ensure_p0_contract_registry(connection: sqlite3.Connection) -> None:
    connection.executescript(
        '''
        CREATE TABLE IF NOT EXISTS roadmap_p0_contracts(
            item_id INTEGER PRIMARY KEY,
            domain_id INTEGER NOT NULL,
            domain_name TEXT NOT NULL,
            action TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'CONTRACTED',
            source_of_truth TEXT NOT NULL DEFAULT 'SQL_GAMESTATE',
            contract_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS roadmap_p0_contract_audit(
            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            allowed INTEGER NOT NULL,
            reason TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(item_id, action)
        );
        CREATE INDEX IF NOT EXISTS idx_roadmap_p0_domain_action ON roadmap_p0_contracts(domain_id, action, status);
        CREATE INDEX IF NOT EXISTS idx_roadmap_p0_audit_item ON roadmap_p0_contract_audit(item_id, audit_id);
        '''
    )
    now = _now()
    for domain_id, domain_name in P0_DOMAINS.items():
        for item_id in range(941 + (domain_id - 1) * 100, 941 + (domain_id - 1) * 100 + 10):
            action = _action_for_item(item_id)
            contract = {'item_id': item_id, 'domain_id': domain_id, 'domain_name': domain_name, 'action': action, 'source_of_truth': 'SQL_GAMESTATE', 'schema_version': P0_SCHEMA_VERSION}
            connection.execute(
                'INSERT OR IGNORE INTO roadmap_p0_contracts(item_id,domain_id,domain_name,action,status,source_of_truth,contract_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',
                (item_id, domain_id, domain_name, action, 'CONSOLIDATED', 'SQL_GAMESTATE', json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(',', ':')), now, now),
            )
    connection.execute("UPDATE roadmap_p0_contracts SET status='CONSOLIDATED', updated_at=? WHERE status='CONTRACTED'", (now,))
    connection.commit()


def validate_p0_contract(connection: sqlite3.Connection, item_id: int) -> dict[str, Any]:
    row = connection.execute('SELECT * FROM roadmap_p0_contracts WHERE item_id=?', (item_id,)).fetchone()
    if row is None:
        raise ValueError('P0_CONTRACT_NOT_FOUND')
    contract = json.loads(row['contract_json'])
    checks = {
        'item_id': int(contract.get('item_id')) == int(item_id),
        'domain_id': int(contract.get('domain_id')) in P0_DOMAINS,
        'action': contract.get('action') in P0_ACTIONS,
        'source_of_truth': contract.get('source_of_truth') == 'SQL_GAMESTATE',
        'schema_version': contract.get('schema_version') == P0_SCHEMA_VERSION,
    }
    return {'status': 'VALID' if all(checks.values()) else 'INVALID', 'item_id': item_id, 'checks': checks, 'contract': contract, 'read_only': True}


def read_p0_contracts(connection: sqlite3.Connection, domain_id: int | None = None) -> list[dict[str, Any]]:
    if domain_id is None:
        rows = connection.execute('SELECT * FROM roadmap_p0_contracts ORDER BY item_id').fetchall()
    else:
        rows = connection.execute('SELECT * FROM roadmap_p0_contracts WHERE domain_id=? ORDER BY item_id', (domain_id,)).fetchall()
    return [{**dict(row), 'contract_json': json.loads(row['contract_json'])} for row in rows]


def protect_p0_mutation(connection: sqlite3.Connection, item_id: int, actor: str, payload: dict[str, Any]) -> dict[str, Any]:
    validation = validate_p0_contract(connection, item_id)
    allowed = bool(actor and actor == 'AUTHORIZED_SQL_SERVICE' and validation['status'] == 'VALID')
    reason = 'ALLOWED' if allowed else 'SQL_SERVICE_AUTHORIZATION_REQUIRED'
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    connection.execute('INSERT OR REPLACE INTO roadmap_p0_contract_audit(item_id,action,allowed,reason,payload,created_at) VALUES(?,?,?,?,?,?)', (item_id, 'PROTECT_MUTATION', int(allowed), reason, serialized, _now()))
    connection.commit()
    if not allowed:
        raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    return {'allowed': True, 'item_id': item_id, 'reason': reason, 'payload_hash': hashlib.sha256(serialized.encode()).hexdigest()}


def audit_p0_contracts(connection: sqlite3.Connection) -> dict[str, Any]:
    rows = connection.execute('SELECT item_id,domain_id,action,status,source_of_truth,contract_json FROM roadmap_p0_contracts ORDER BY item_id').fetchall()
    item_ids = [int(row['item_id']) for row in rows]
    checks = {'count_300': len(rows) == 300, 'unique_items': len(set(item_ids)) == len(rows), 'all_consolidated': all(row['status'] == 'CONSOLIDATED' for row in rows), 'sql_game_state': all(row['source_of_truth'] == 'SQL_GAMESTATE' for row in rows), 'valid_contracts': True}
    invalid_items = []
    for row in rows:
        try:
            contract = json.loads(row['contract_json'])
            valid = (int(contract.get('item_id')) == int(row['item_id']) and int(contract.get('domain_id')) in P0_DOMAINS and contract.get('action') in P0_ACTIONS and contract.get('source_of_truth') == 'SQL_GAMESTATE' and contract.get('schema_version') == P0_SCHEMA_VERSION)
            if not valid: invalid_items.append(int(row['item_id']))
        except (TypeError, ValueError, json.JSONDecodeError):
            invalid_items.append(int(row['item_id']))
    checks['valid_contracts'] = not invalid_items
    return {'status': 'VALID' if all(checks.values()) else 'INVALID', 'contract_count': len(rows), 'checks': checks, 'invalid_items': invalid_items, 'read_only': True}
