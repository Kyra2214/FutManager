from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine.rules.state_store import CareerStateStore
from engine.rules.backup import StateBackupService

BASE=ROOT/'data/database/game.db'

def clone_base(path):
    source=sqlite3.connect(BASE); target=sqlite3.connect(path); source.backup(target); source.close(); target.close()

def test_save_close_reopen_and_backup_restore():
    with tempfile.TemporaryDirectory() as d:
        state=Path(d)/'game.db'; clone_base(state)
        store=CareerStateStore(state)
        cid=store.create_player(player_id=None,country_id=29,club_id=1,seed=9)
        store.close()
        reopened=CareerStateStore(state)
        assert reopened.connection.execute('select count(*) from player_career_state').fetchone()[0]==1
        backup=StateBackupService(state).create_backup('test')
        assert backup.exists()
        reopened.close()
