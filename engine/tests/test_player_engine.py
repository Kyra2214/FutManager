from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from engine.core.engine import FootballManagerEngine
from engine.players.domain import Player, Position, PlayerStatus

DB = ROOT / "data/database/game.db"
STATE = ROOT / "data/state/game.db"


def test_player_engine_returns_domain_objects(tmp_path):
    state = tmp_path / 'game.db'
    shutil.copy2(DB, state)
    engine = FootballManagerEngine(state).open()
    found = engine.players.search("Neymar", limit=5)
    assert found
    assert all(isinstance(player, Player) for player in found)
    assert all(isinstance(player.position, Position) for player in found)
    engine.close()


def test_native_attributes_are_preserved_separately():
    engine = FootballManagerEngine(STATE).open()
    row = engine.database.open().execute("SELECT * FROM jogadores WHERE rating_hash IS NOT NULL LIMIT 1").fetchone()
    player = engine.players.get(row["jogador_id"])
    assert player is not None
    assert player.native.rating_hash == row["rating_hash"]
    assert player.strength is None
    assert player.potential is None
    engine.close()


def test_position_labels_are_confirmed():
    assert [Position(i).label for i in range(5)] == ["Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante"]
