from pathlib import Path
import sqlite3
import tempfile

from engine.core.state_store import configure_state_connection
from engine.manager.career import SCHEMA
from engine.core.p0_contracts import ensure_p0_contract_registry

path = Path(tempfile.mktemp(suffix='.db'))
print('path', path, flush=True)
connection = sqlite3.connect(path)
print('connected', flush=True)
configure_state_connection(connection)
print('configured', flush=True)
connection.executescript(SCHEMA)
print('career_schema', flush=True)
ensure_p0_contract_registry(connection)
print('p0_registry', flush=True)
print(connection.execute('SELECT count(*) FROM roadmap_p0_contracts').fetchone()[0], flush=True)
connection.close()
path.unlink(missing_ok=True)
