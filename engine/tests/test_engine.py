from pathlib import Path
import hashlib
import shutil
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine.core.engine import FootballManagerEngine
from engine.core.state import GameState

DB = ROOT / "data/database/game.db"
STATE = ROOT / "data/state/game.db"


def test_original_and_state_copy_exist():
    assert DB.exists()
    assert STATE.exists()
    assert hashlib.sha256(DB.read_bytes()).hexdigest() == (ROOT / "data/database/game.db.sha256").read_text().strip()
    assert STATE.stat().st_size >= DB.stat().st_size


def test_sqlite_integrity_and_foreign_keys():
    con = sqlite3.connect(DB)
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []
    con.close()


def test_expected_dataset_counts():
    con = sqlite3.connect(DB)
    assert con.execute("SELECT COUNT(*) FROM jogadores").fetchone()[0] == 231911
    assert con.execute("SELECT COUNT(*) FROM times").fetchone()[0] == 8399
    assert con.execute("SELECT COUNT(*) FROM paises").fetchone()[0] == 224
    assert con.execute("SELECT COUNT(*) FROM jogador_time").fetchone()[0] == 235722
    assert con.execute("SELECT COUNT(*) - COUNT(DISTINCT chave_canonica) FROM jogadores").fetchone()[0] == 0
    con.close()


def test_positions_and_repositories(tmp_path):
    state = tmp_path / 'game.db'
    shutil.copy2(DB, state)
    engine = FootballManagerEngine(state).open()
    assert {r[0] for r in engine.database.open().execute("SELECT DISTINCT posicao_codigo FROM jogadores")} == {0,1,2,3,4}
    assert engine.players.search("Neymar", limit=5)
    assert engine.teams.search("Flamengo", limit=5)
    engine.close()


def test_game_state_initializes(tmp_path):
    state_path = tmp_path / 'game.db'
    shutil.copy2(DB, state_path)
    state = GameState.initialize(state_path)
    assert state.database_path == state_path
    assert state.current_season == "inicial"
