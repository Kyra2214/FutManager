import sqlite3
from engine.core.state_manifest import StateManifestService

def test_state_manifest_migration_checksum_drift_snapshot_and_fk():
    connection = sqlite3.connect(':memory:')
    connection.execute('CREATE TABLE parent(id INTEGER PRIMARY KEY)')
    connection.execute('CREATE TABLE child(id INTEGER PRIMARY KEY,parent_id INTEGER REFERENCES parent(id))')
    service = StateManifestService(connection)
    assert service.validate_foreign_keys()['valid'] is True
    first = service.migrate_v4()
    assert first['to_version'] == 4 and first['status'] == 'APPLIED'
    assert service.migrate_v4()['status'] == 'ALREADY_APPLIED'
    assert service.drift()['drift'] is False
    snapshot = service.snapshot('before-change')
    assert snapshot['schema_version'] == 4 and snapshot['payload']['tables']
    assert service.restore_selective(snapshot['snapshot_id'], ['parent'])['restored'] is False
    try:
        service.restore_selective(snapshot['snapshot_id'], ['missing'])
    except ValueError as error:
        assert str(error) == 'UNKNOWN_TABLE:missing'
    else:
        raise AssertionError('unknown table accepted')
    service.close()
