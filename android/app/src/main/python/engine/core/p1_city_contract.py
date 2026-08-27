import hashlib
import json
from datetime import datetime, timezone

from engine.core.domain_errors import DomainError, DomainErrorCode

ITEM_IDS = tuple(range(1261, 1271))
ACTIONS = ("DEFINE_CONTRACT", "VALIDATE_RULES", "PERSIST_STATE", "EXPOSE_READ", "PROTECT_MUTATION", "AUDIT_FLOW", "OPTIMIZE_QUERY", "SIMULATE_SCENARIO", "DOCUMENT_CYCLE", "TEST_INTEGRATION")


def _now():
    return datetime.now(timezone.utc).isoformat()


def ensure_p1_city_registry(connection):
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS roadmap_p1_city_contracts (
      item_id INTEGER PRIMARY KEY, domain_id INTEGER NOT NULL, city_name TEXT NOT NULL,
      payload_schema TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'CONSOLIDATED',
      source_of_truth TEXT NOT NULL DEFAULT 'SQL_GAMESTATE', contract_json TEXT NOT NULL,
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS roadmap_p1_cities (
      city_key TEXT PRIMARY KEY, city_id INTEGER NOT NULL, country_id INTEGER,
      city_name TEXT NOT NULL, status TEXT NOT NULL, payload_json TEXT NOT NULL,
      payload_hash TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS roadmap_p1_city_audit (
      audit_id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL,
      action TEXT NOT NULL, allowed INTEGER NOT NULL, reason TEXT NOT NULL,
      payload TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(item_id, action)
    );
    CREATE INDEX IF NOT EXISTS idx_p1_cities_lookup ON roadmap_p1_cities(country_id, status, updated_at);
    """)
    now = _now()
    for item_id, action in zip(ITEM_IDS, ACTIONS):
        contract = {'item_id': item_id, 'domain_id': 4, 'city_name': 'city_state', 'payload_schema': 'city_key,city_id,country_id,city_name,status,payload', 'action': action, 'source_of_truth': 'SQL_GAMESTATE', 'schema_version': 1}
        connection.execute('INSERT OR IGNORE INTO roadmap_p1_city_contracts VALUES(?,?,?,?,?,?,?,?,?)', (item_id, 4, 'city_state', contract['payload_schema'], 'CONSOLIDATED', 'SQL_GAMESTATE', json.dumps(contract, sort_keys=True, separators=(',', ':')), now, now))
    connection.commit()


def validate_p1_city(connection, item_id):
    row = connection.execute('SELECT * FROM roadmap_p1_city_contracts WHERE item_id=?', (item_id,)).fetchone()
    if row is None:
        raise ValueError('P1_CITY_NOT_FOUND')
    contract = json.loads(row['contract_json'])
    checks = {'item_id': contract.get('item_id') == item_id, 'domain_id': contract.get('domain_id') == 4, 'city_name': contract.get('city_name') == 'city_state', 'action': contract.get('action') in ACTIONS, 'source_of_truth': contract.get('source_of_truth') == 'SQL_GAMESTATE'}
    return {'status': 'VALID' if all(checks.values()) else 'INVALID', 'item_id': item_id, 'checks': checks, 'contract': contract, 'read_only': True}


def read_p1_cities(connection):
    return [{**dict(row), 'contract_json': json.loads(row['contract_json'])} for row in connection.execute('SELECT * FROM roadmap_p1_city_contracts ORDER BY item_id')]


def persist_p1_city(connection, key, city_id, city_name, payload, country_id=None, status='ACTIVE', actor=''):
    if actor != 'AUTHORIZED_SQL_SERVICE':
        raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    if not key.strip() or int(city_id) < 0 or (country_id is not None and int(country_id) < 0) or not city_name.strip() or status not in {'ACTIVE', 'INACTIVE', 'PENDING'} or not isinstance(payload, dict):
        raise ValueError('P1_CITY_PAYLOAD_INVALID')
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    now = _now()
    connection.execute('INSERT INTO roadmap_p1_cities(city_key,city_id,country_id,city_name,status,payload_json,payload_hash,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(city_key) DO UPDATE SET city_id=excluded.city_id,country_id=excluded.country_id,city_name=excluded.city_name,status=excluded.status,payload_json=excluded.payload_json,payload_hash=excluded.payload_hash,updated_at=excluded.updated_at', (key.strip(), int(city_id), country_id, city_name.strip(), status, encoded, digest, now, now))
    connection.commit()
    row = connection.execute('SELECT * FROM roadmap_p1_cities WHERE city_key=?', (key.strip(),)).fetchone()
    return {**dict(row), 'payload_json': json.loads(row['payload_json'])}


def read_p1_city_state(connection, key=None):
    clause = ' WHERE city_key=?' if key else ''
    args = (key,) if key else ()
    return [{**dict(row), 'payload_json': json.loads(row['payload_json'])} for row in connection.execute('SELECT * FROM roadmap_p1_cities' + clause + ' ORDER BY updated_at DESC', args)]


def audit_p1_cities(connection):
    rows = read_p1_cities(connection)
    invalid = [row['item_id'] for row in rows if validate_p1_city(connection, row['item_id'])['status'] != 'VALID']
    checks = {'count_10': len(rows) == 10, 'expected_ids': {row['item_id'] for row in rows} == set(ITEM_IDS), 'all_consolidated': all(row['status'] == 'CONSOLIDATED' for row in rows), 'sql_game_state': all(row['source_of_truth'] == 'SQL_GAMESTATE' for row in rows), 'valid_contracts': not invalid}
    return {'status': 'VALID' if all(checks.values()) else 'INVALID', 'city_count': len(rows), 'state_count': connection.execute('SELECT COUNT(*) FROM roadmap_p1_cities').fetchone()[0], 'checks': checks, 'invalid_items': invalid, 'read_only': True}


def protect_p1_city_mutation(connection, item_id, actor, payload):
    valid = validate_p1_city(connection, item_id)
    allowed = actor == 'AUTHORIZED_SQL_SERVICE' and valid['status'] == 'VALID'
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    connection.execute('INSERT OR REPLACE INTO roadmap_p1_city_audit(item_id,action,allowed,reason,payload,created_at) VALUES(?,?,?,?,?,?)', (item_id, 'PROTECT_MUTATION', int(allowed), 'ALLOWED' if allowed else 'SQL_SERVICE_AUTHORIZATION_REQUIRED', encoded, _now()))
    connection.commit()
    if not allowed:
        raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
    return {'allowed': True, 'item_id': item_id, 'payload_hash': hashlib.sha256(encoded.encode()).hexdigest()}
