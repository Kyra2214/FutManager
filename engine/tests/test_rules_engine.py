from pathlib import Path
import hashlib
import sqlite3
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from engine.rules.player_rules import CareerRulesConfig, CareerStatus, PlayerRules
from engine.rules.state_store import CareerStateStore

BASE=ROOT/'data/database/game.db'


def test_new_player_starts_at_16_and_seed_is_reproducible():
    rules=PlayerRules()
    assert rules.generate_potential(11)==rules.generate_potential(11)
    assert 1 <= rules.generate_potential(11) <= 99
    with tempfile.TemporaryDirectory() as d:
        state=Path(d)/'game.db'; sqlite3.connect(BASE).backup(sqlite3.connect(state))
        store=CareerStateStore(state)
        cid=store.create_player(player_id=None,country_id=29,club_id=None,seed=11,rules=rules)
        row=store.connection.execute('select * from player_career_state where career_id=?',(cid,)).fetchone()
        assert row['age']==16 and row['status']==CareerStatus.YOUTH.value
        assert 1 <= row['potential'] <= 99
        store.close()


def test_strength_is_bounded_by_potential_and_curve_is_smooth():
    rules=PlayerRules()
    values=[rules.calculate_strength(99,a) for a in range(16,36)]
    assert max(values)<=99 and min(values)>=1
    assert values[10] >= values[0]
    assert values[-1] >= 1
    assert abs(values[15]-values[14]) <= 10


def test_retirement_return_and_new_generation():
    with tempfile.TemporaryDirectory() as d:
        state=Path(d)/'game.db'; sqlite3.connect(BASE).backup(sqlite3.connect(state))
        store=CareerStateStore(state); rules=PlayerRules()
        cid=store.create_player(player_id=None,country_id=29,club_id=1,seed=3)
        for _ in range(20): store.age_player(cid,rules)
        store.retire(cid)
        old=store.connection.execute('select * from player_career_state where career_id=?',(cid,)).fetchone()
        assert old['status']=='RETIRED' and old['current_club_id'] is None
        store.increment_season_out(cid)
        new_id=store.return_generation(cid,club_id=2,seed=4)
        new=store.connection.execute('select * from player_career_state where career_id=?',(new_id,)).fetchone()
        assert new['age']==16 and new['generation']==2 and new['current_club_id']==2
        store.close()


def test_transaction_rolls_back():
    with tempfile.TemporaryDirectory() as d:
        state=Path(d)/'game.db'; sqlite3.connect(BASE).backup(sqlite3.connect(state))
        store=CareerStateStore(state)
        try:
            with store.transaction() as con:
                con.execute("insert into world_state(world_id,current_date,current_season,updated_at) values (1,'bad','bad','bad')")
                con.execute("insert into world_state(world_id,current_date,current_season,updated_at) values (1,'duplicate','bad','bad')")
        except sqlite3.IntegrityError: pass
        assert store.connection.execute('select count(*) from world_state').fetchone()[0]==0
        store.close()


def test_base_hash_unchanged():
    assert hashlib.sha256(BASE.read_bytes()).hexdigest()==Path(ROOT/'data/database/game.db.sha256').read_text().strip()
