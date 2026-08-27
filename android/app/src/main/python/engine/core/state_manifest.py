from __future__ import annotations
from datetime import datetime, timezone
import hashlib, json, sqlite3
from engine.core.state_store import assert_mutable_state_path

SCHEMA = '''
CREATE TABLE IF NOT EXISTS state_schema_manifest(version INTEGER PRIMARY KEY, checksum TEXT NOT NULL, applied_at TEXT NOT NULL, source TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS state_migrations(migration_id TEXT PRIMARY KEY, from_version INTEGER NOT NULL, to_version INTEGER NOT NULL, checksum TEXT NOT NULL, applied_at TEXT NOT NULL, status TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS state_snapshots(snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT NOT NULL, schema_version INTEGER NOT NULL, checksum TEXT NOT NULL, created_at TEXT NOT NULL, payload TEXT NOT NULL, UNIQUE(label, checksum));
CREATE INDEX IF NOT EXISTS idx_state_migrations_version ON state_migrations(to_version, applied_at);
CREATE INDEX IF NOT EXISTS idx_state_snapshots_created ON state_snapshots(created_at DESC);
'''

class StateManifestService:
    def __init__(self, db):
        if not isinstance(db, sqlite3.Connection):
            assert_mutable_state_path(db)
        self.connection = sqlite3.connect(str(db)) if not isinstance(db, sqlite3.Connection) else db
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys=ON')
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def inventory(self) -> list[dict]:
        rows = self.connection.execute("SELECT name, type, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name").fetchall()
        return [dict(row) for row in rows]

    def checksum(self) -> str:
        catalog = [{'name': row['name'], 'type': row['type'], 'sql': row['sql']} for row in self.connection.execute("SELECT name,type,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name").fetchall()]
        return hashlib.sha256(json.dumps(catalog, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

    def migrate_v4(self, source='roadmap-701') -> dict:
        current = self.connection.execute('SELECT COALESCE(MAX(version),3) AS version FROM state_schema_manifest').fetchone()['version']
        if int(current) >= 4:
            return {'from_version': int(current), 'to_version': int(current), 'status': 'ALREADY_APPLIED', 'checksum': self.checksum()}
        checksum = self.checksum()
        applied = datetime.now(timezone.utc).isoformat()
        with self.connection:
            self.connection.execute('INSERT OR REPLACE INTO state_schema_manifest(version,checksum,applied_at,source) VALUES(?,?,?,?)',(4,checksum,applied,source))
            self.connection.execute('INSERT OR REPLACE INTO state_migrations(migration_id,from_version,to_version,checksum,applied_at,status) VALUES(?,?,?,?,?,?)',('schema-v4',int(current),4,checksum,applied,'APPLIED'))
        return {'from_version': int(current), 'to_version': 4, 'status': 'APPLIED', 'checksum': checksum}

    def drift(self) -> dict:
        current = self.checksum()
        latest = self.connection.execute('SELECT checksum,version FROM state_schema_manifest ORDER BY version DESC LIMIT 1').fetchone()
        return {'drift': bool(latest and latest['checksum'] != current), 'current_checksum': current, 'manifest_checksum': latest['checksum'] if latest else None, 'schema_version': latest['version'] if latest else None}

    def validate_foreign_keys(self) -> dict:
        errors = [dict(row) for row in self.connection.execute('PRAGMA foreign_key_check').fetchall()]
        return {'valid': not errors, 'errors': errors, 'count': len(errors)}

    def snapshot(self, label: str) -> dict:
        payload = {'tables': [{'name': row['name'], 'count': int(self.connection.execute(f"SELECT COUNT(*) FROM [{row['name']}]").fetchone()[0])} for row in self.connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()]}
        checksum = self.checksum(); version = self.connection.execute('SELECT COALESCE(MAX(version),3) FROM state_schema_manifest').fetchone()[0]
        with self.connection:
            cur = self.connection.execute('INSERT OR IGNORE INTO state_snapshots(label,schema_version,checksum,created_at,payload) VALUES(?,?,?,?,?)',(str(label),int(version),checksum,datetime.now(timezone.utc).isoformat(),json.dumps(payload,sort_keys=True)))
        return {'snapshot_id': int(cur.lastrowid or self.connection.execute('SELECT snapshot_id FROM state_snapshots WHERE label=? AND checksum=?',(label,checksum)).fetchone()[0]), 'label': label, 'schema_version': int(version), 'checksum': checksum, 'payload': payload}

    def restore_selective(self, snapshot_id: int, tables: list[str]) -> dict:
        row = self.connection.execute('SELECT * FROM state_snapshots WHERE snapshot_id=?',(int(snapshot_id),)).fetchone()
        if not row: raise KeyError(snapshot_id)
        known = {item['name'] for item in self.inventory()}
        unknown = [table for table in tables if table not in known]
        if unknown: raise ValueError(f'UNKNOWN_TABLE:{unknown[0]}')
        return {'snapshot_id': int(snapshot_id), 'tables': list(tables), 'restored': False, 'reason': 'snapshot metadata only; data writers remain explicit'}

    def close(self):
        self.connection.close()
