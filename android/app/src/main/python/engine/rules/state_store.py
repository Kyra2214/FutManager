from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from pathlib import Path
import json
import sqlite3
import shutil

from engine.rules.player_rules import CareerStatus, PlayerRules


STATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS world_state (
    world_id INTEGER PRIMARY KEY CHECK(world_id=1),
    current_date TEXT NOT NULL,
    current_season TEXT NOT NULL,
    seed INTEGER,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS player_career_state (
    career_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER,
    generation INTEGER NOT NULL DEFAULT 1,
    age INTEGER NOT NULL,
    status TEXT NOT NULL,
    current_club_id INTEGER,
    birth_club_id INTEGER,
    career_club_id INTEGER,
    potential INTEGER,
    current_strength INTEGER,
    development_factor REAL,
    seasons_out INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(player_id) REFERENCES jogadores(jogador_id)
);
CREATE TABLE IF NOT EXISTS career_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    career_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    event_date TEXT NOT NULL,
    payload TEXT NOT NULL,
    FOREIGN KEY(career_id) REFERENCES player_career_state(career_id)
);
CREATE TABLE IF NOT EXISTS audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    entity_id INTEGER,
    event_date TEXT NOT NULL,
    payload TEXT NOT NULL
);
"""


class CareerStateStore:
    def __init__(self, state_db: str | Path):
        from engine.core.state_store import assert_mutable_state_path
        assert_mutable_state_path(state_db)
        self.path = Path(state_db)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(STATE_SCHEMA)
        self.connection.commit()

    @contextmanager
    def transaction(self):
        try:
            self.connection.execute("BEGIN")
            yield self.connection
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise

    def create_player(self, *, player_id: int | None, country_id: int | None, club_id: int | None,
                      seed: int | None = None, rules: PlayerRules | None = None) -> int:
        rules = rules or PlayerRules()
        age = rules.config.starting_age
        rules.validate_new_age(age)
        potential = rules.generate_potential(seed)
        strength = rules.calculate_strength(potential, age)
        with self.transaction() as con:
            cur = con.execute("""INSERT INTO player_career_state
                (player_id,generation,age,status,current_club_id,birth_club_id,career_club_id,potential,current_strength,development_factor)
                VALUES (?,?,?,?,?,?,?,?,?,?)""", (player_id, 1, age, CareerStatus.YOUTH.value, club_id, club_id, club_id, potential, strength, rules.development_factor(age)))
            career_id = cur.lastrowid
            self._event(con, career_id, "PLAYER_CREATED", {"country_id": country_id, "age": age, "seed": seed})
            return int(career_id)

    def age_player(self, career_id: int, rules: PlayerRules | None = None) -> sqlite3.Row:
        rules = rules or PlayerRules()
        with self.transaction() as con:
            row = con.execute("SELECT * FROM player_career_state WHERE career_id=?", (career_id,)).fetchone()
            if row is None: raise KeyError(career_id)
            age = row["age"] + 1
            status = rules.next_status(age, CareerStatus(row["status"]))
            strength = rules.calculate_strength(row["potential"], age)
            con.execute("UPDATE player_career_state SET age=?,status=?,current_strength=?,development_factor=? WHERE career_id=?", (age,status.value,strength,rules.development_factor(age),career_id))
            self._event(con, career_id, "PLAYER_AGED", {"age": age, "status": status.value})
            return con.execute("SELECT * FROM player_career_state WHERE career_id=?", (career_id,)).fetchone()

    def retire(self, career_id: int) -> None:
        with self.transaction() as con:
            row = con.execute("SELECT status FROM player_career_state WHERE career_id=?", (career_id,)).fetchone()
            if row is None: raise KeyError(career_id)
            con.execute("UPDATE player_career_state SET status=?,current_club_id=NULL WHERE career_id=?", (CareerStatus.RETIRED.value,career_id))
            self._event(con, career_id, "PLAYER_RETIRED", {})

    def return_generation(self, career_id: int, club_id: int | None, seed: int | None = None, rules: PlayerRules | None = None) -> int:
        rules = rules or PlayerRules()
        with self.transaction() as con:
            row = con.execute("SELECT * FROM player_career_state WHERE career_id=?", (career_id,)).fetchone()
            if row is None: raise KeyError(career_id)
            if not rules.can_return(CareerStatus(row["status"]), row["seasons_out"]): raise ValueError("período mínimo fora da carreira ainda não cumprido")
            potential = rules.generate_potential(seed)
            strength = rules.calculate_strength(potential, rules.config.starting_age)
            cur=con.execute("""INSERT INTO player_career_state
                (player_id,generation,age,status,current_club_id,birth_club_id,career_club_id,potential,current_strength,development_factor,seasons_out)
                VALUES (?,?,?,?,?,?,?,?,?,?,0)""", (row["player_id"], row["generation"]+1, rules.config.starting_age, CareerStatus.RETURNED.value, club_id, club_id, club_id, potential, strength, rules.development_factor(rules.config.starting_age)))
            new_id=cur.lastrowid
            self._event(con,new_id,"PLAYER_RETURNED",{"previous_career_id":career_id,"club_id":club_id,"seed":seed})
            return int(new_id)

    def increment_season_out(self, career_id: int) -> None:
        with self.transaction() as con:
            con.execute("UPDATE player_career_state SET seasons_out=seasons_out+1 WHERE career_id=? AND status=?", (career_id,CareerStatus.RETIRED.value))

    def _event(self, con, career_id: int, event_type: str, payload: dict):
        today=date.today().isoformat()
        body=json.dumps(payload, ensure_ascii=False, sort_keys=True)
        con.execute("INSERT INTO career_events(career_id,event_type,event_date,payload) VALUES (?,?,?,?)",(career_id,event_type,today,body))
        con.execute("INSERT INTO audit_log(event_type,entity_id,event_date,payload) VALUES (?,?,?,?)",(event_type,career_id,today,body))

    def close(self):
        self.connection.close()
