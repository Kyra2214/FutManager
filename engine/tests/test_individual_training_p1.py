from __future__ import annotations

import sqlite3

from engine.sports.training import TrainingService


def make_db():
    con = sqlite3.connect(':memory:')
    con.executescript('''
      CREATE TABLE times(time_id INTEGER PRIMARY KEY);
      CREATE TABLE jogadores(jogador_id INTEGER PRIMARY KEY,nome TEXT,cr2 INTEGER);
      CREATE TABLE jogador_time(jogador_id INTEGER,time_id INTEGER);
      CREATE TABLE player_sport_state(player_id INTEGER PRIMARY KEY,condition INTEGER,fatigue INTEGER,form INTEGER);
      CREATE TABLE injuries(injury_id INTEGER PRIMARY KEY,player_id INTEGER,status TEXT);
      CREATE TABLE staff_members(staff_id INTEGER PRIMARY KEY,club_id INTEGER,role TEXT,level INTEGER,status TEXT);
      CREATE TABLE club_departments(club_id INTEGER,department TEXT,level INTEGER,cost INTEGER,capacity INTEGER,maintenance INTEGER,efficiency REAL,PRIMARY KEY(club_id,department));
      INSERT INTO times VALUES(1); INSERT INTO jogadores VALUES(10,'Atleta',80); INSERT INTO jogador_time VALUES(10,1);
      INSERT INTO player_sport_state VALUES(10,90,10,60);
    ''')
    return TrainingService(con)


def test_individual_training_preview_approval_and_evolution_are_idempotent():
    service = make_db()
    plan = service.create_individual_plan(1, 10, 2026, 'técnica', 40)
    preview = service.preview_individual_plan(plan['individual_plan_id'])
    assert preview['preview']['persisted'] is False
    approved = service.approve_individual_plan(plan['individual_plan_id'])
    assert approved['status'] == 'APPROVED'
    first = service.record_evolution(1, 10, 2026, 1.5, 'microciclo', 'evo-1')
    second = service.record_evolution(1, 10, 2026, 1.5, 'microciclo', 'evo-1')
    assert first['evolution_id'] == second['evolution_id']
    service.close()


def test_individual_training_blocks_extreme_medical_risk():
    service = make_db()
    service.connection.execute('UPDATE player_sport_state SET condition=10,fatigue=100 WHERE player_id=10')
    service.connection.commit()
    plan = service.create_individual_plan(1, 10, 2026, 'físico', 100)
    assert service.approve_individual_plan(plan['individual_plan_id'])['status'] == 'BLOCKED_MEDICAL_RISK'
    service.close()
