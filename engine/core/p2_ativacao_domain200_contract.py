import hashlib
import json
from datetime import datetime, timezone

from engine.core.domain_errors import DomainError, DomainErrorCode

ITEM_IDS = tuple(range(1281, 1291))
ACTIONS = ("DEFINE_CONTRACT", "VALIDATE_RULES", "PERSIST_STATE", "EXPOSE_READ", "PROTECT_MUTATION", "AUDIT_FLOW", "OPTIMIZE_QUERY", "SIMULATE_SCENARIO", "DOCUMENT_CYCLE", "TEST_INTEGRATION")


def _now():
    return datetime.now(timezone.utc).isoformat()


def ensure_p2_ativacao_domain200_registry(connection):
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS roadmap_p1_ativacao_domain200_contracts (
      item_id INTEGER PRIMARY KEY, domain_id INTEGER NOT NULL, ativacao_domain200_name TEXT NOT NULL,
      payload_schema TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'CONSOLIDATED',
      source_of_truth TEXT NOT NULL DEFAULT 'SQL_GAMESTATE', contract_json TEXT NOT NULL,
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS roadmap_p1_ativacao_domain200s (
      ativacao_domain200_key TEXT PRIMARY KEY, ativacao_domain200_id INTEGER NOT NULL, manager_id INTEGER,
      ativacao_domain200_name TEXT NOT NULL, status TEXT NOT NULL, payload_json TEXT NOT NULL,
      payload_hash TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS roadmap_p1_ativacao_domain200_audit (
      audit_id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
      action TEXT NOT NULL, allowed INTEGER NOT NULL, reason TEXT NOT NULL,
      payload TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(item_id, action)
    );
    CREATE INDEX IF NOT EXISTS idx_p1_ativacao_domain200s_lookup ON roadmap_p1_ativacao_domain200s(manager_id, status, updated_at);
    """)
    now = _now()
    for item_id, action in zip(ITEM_IDS, ACTIONS):
        contract = {'item_id': item_id, 'domain_id': 4, 'ativacao_domain200_name': 'ativacao_domain200_state', 'payload_schema': 'ativacao_domain200_key,ativacao_domain200_id,manager_id,ativacao_domain200_name,status,payload', 'action': action, 'source_of_truth': 'SQL_GAMESTATE', 'schema_version': 1}
        connection.execute('INSERT OR IGNORE INTO roadmap_p1_ativacao_domain200_contracts VALUES(?,?,?,?,?,?,?,?,?)', (item_id, 4, 'ativacao_domain200_state', contract['payload_schema'], 'CONSOLIDATED', 'SQL_GAMESTATE', json.dumps(contract, sort_keys=True, separators=(',', ':')), now, now))
    connection.commit()


def validate_p1_ativacao_domain200(connection, item_id):
    row = connection.execute('SELECT * FROM roadmap_p1_ativacao_domain200_contracts WHERE item_id=?', (item_id,)).fetchone()
    if row is None:
        raise ValueError('P2_ATIVACAO_DOMAIN200_NOT_FOUND')
    contract = json.loads(row['contract_json'])
    checks = {'item_id': contract.get('item_id') == item_id, 'domain_id': contract.get('domain_id') == 4, 'ativacao_domain200_name': contract.get('ativacao_domain200_name') == 'ativacao_domain200_state', 'action': contract.get('action') in ACTIONS, 'source_of_truth': contract.get('source_of_truth') == 'SQL_GAMESTATE'}
    return {'status': 'VALID' if all(checks.values()) else 'INVALID', 'item_id': item_id, 'checks': checks, 'contract': contract, 'read_only': True}


def read_p1_ativacao_domain200s(connection):
    return [{**dict(row), 'contract_json': json.loads(row['contract_json'])} for row in connection.execute('SELECT * FROM roadmap_p1_ativacao_domain200_contracts ORDER BY item_id')]


def persist_p1_ativacao_domain200(connection, key, ativacao_domain200_id, ativacao_domain200_name, payload, manager_id=None, status='ACTIVE', actor=''):
    if actor != 'AUTHORIZED_SQL_SERVICE':
        raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    if not key.strip() or int(ativacao_domain200_id) < 0 or (manager_id is not None and int(manager_id) < 0) or not ativacao_domain200_name.strip() or status not in {'ACTIVE', 'INACTIVE', 'PENDING'} or not isinstance(payload, dict):
        raise ValueError('P2_ATIVACAO_DOMAIN200_PAYLOAD_INVALID')
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    now = _now()
    connection.execute('INSERT INTO roadmap_p1_ativacao_domain200s(ativacao_domain200_key,ativacao_domain200_id,manager_id,ativacao_domain200_name,status,payload_json,payload_hash,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(ativacao_domain200_key) DO UPDATE SET ativacao_domain200_id=excluded.ativacao_domain200_id,manager_id=excluded.manager_id,ativacao_domain200_name=excluded.ativacao_domain200_name,status=excluded.status,payload_json=excluded.payload_json,payload_hash=excluded.payload_hash,updated_at=excluded.updated_at', (key.strip(), int(ativacao_domain200_id), manager_id, ativacao_domain200_name.strip(), status, encoded, digest, now, now))
    connection.commit()
    row = connection.execute('SELECT * FROM roadmap_p1_ativacao_domain200s WHERE ativacao_domain200_key=?', (key.strip(),)).fetchone()
    return {**dict(row), 'payload_json': json.loads(row['payload_json'])}


def read_p1_ativacao_domain200_state(connection, key=None):
    clause = ' WHERE ativacao_domain200_key=?' if key else ''
    args = (key,) if key else ()
    return [{**dict(row), 'payload_json': json.loads(row['payload_json'])} for row in connection.execute('SELECT * FROM roadmap_p1_ativacao_domain200s' + clause + ' ORDER BY updated_at DESC', args)]


def audit_p2_ativacao_domain200s(connection):
    rows = read_p1_ativacao_domain200s(connection)
    invalid = [row['item_id'] for row in rows if validate_p1_ativacao_domain200(connection, row['item_id'])['status'] != 'VALID']
    checks = {'count_10': len(rows) == 10, 'expected_ids': {row['item_id'] for row in rows} == set(ITEM_IDS), 'all_consolidated': all(row['status'] == 'CONSOLIDATED' for row in rows), 'sql_game_state': all(row['source_of_truth'] == 'SQL_GAMESTATE' for row in rows), 'valid_contracts': not invalid}
    return {'status': 'VALID' if all(checks.values()) else 'INVALID', 'ativacao_domain200_count': len(rows), 'state_count': connection.execute('SELECT COUNT(*) FROM roadmap_p1_ativacao_domain200s').fetchone()[0], 'checks': checks, 'invalid_items': invalid, 'read_only': True}


def protect_p1_ativacao_domain200_mutation(connection, item_id, actor, payload):
    valid = validate_p1_ativacao_domain200(connection, item_id)
    allowed = actor == 'AUTHORIZED_SQL_SERVICE' and valid['status'] == 'VALID'
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    connection.execute('INSERT OR REPLACE INTO roadmap_p1_ativacao_domain200_audit(item_id,action,allowed,reason,payload,created_at) VALUES(?,?,?,?,?,?)', (item_id, 'PROTECT_MUTATION', int(allowed), 'ALLOWED' if allowed else 'SQL_SERVICE_AUTHORIZATION_REQUIRED', encoded, _now()))
    connection.commit()
    if not allowed:
        raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    return {'allowed': True, 'item_id': item_id, 'payload_hash': hashlib.sha256(encoded.encode()).hexdigest()}
