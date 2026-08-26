import sqlite3
from engine.sports.training import TrainingService


def fixture(tmp_path):
    path=tmp_path/'training.db'; con=sqlite3.connect(path)
    con.executescript('''
      CREATE TABLE times(time_id INTEGER PRIMARY KEY);
      CREATE TABLE jogadores(jogador_id INTEGER PRIMARY KEY,nome TEXT,cr2 INTEGER);
      CREATE TABLE jogador_time(jogador_id INTEGER,time_id INTEGER);
      CREATE TABLE player_sport_state(player_id INTEGER PRIMARY KEY,condition INTEGER,fatigue INTEGER,form INTEGER);
      CREATE TABLE injuries(injury_id INTEGER PRIMARY KEY,player_id INTEGER,status TEXT);
      CREATE TABLE staff_members(staff_id INTEGER PRIMARY KEY,club_id INTEGER,role TEXT,level INTEGER,status TEXT);
      CREATE TABLE club_departments(club_id INTEGER,department TEXT,level INTEGER,cost INTEGER,capacity INTEGER,maintenance INTEGER,efficiency REAL,PRIMARY KEY(club_id,department));
      INSERT INTO times VALUES(1);
      INSERT INTO jogadores VALUES(10,'Atleta Saudável',80),(11,'Atleta Lesionado',75);
      INSERT INTO jogador_time VALUES(10,1),(11,1);
      INSERT INTO player_sport_state VALUES(10,100,20,60),(11,70,80,45);
      INSERT INTO injuries VALUES(1,11,'ACTIVE');
      INSERT INTO staff_members VALUES(1,1,'medico',5,'ativo');
      INSERT INTO club_departments VALUES(1,'medicina',2,100,10,0,0.2);
    '''); con.commit(); con.close(); return path


def test_training_plan_is_idempotent_and_respects_injury(tmp_path):
    service=TrainingService(fixture(tmp_path))
    first=service.create_weekly_plan(1,2026,1,'PHYSICAL',80)
    second=service.create_weekly_plan(1,2026,1,'PHYSICAL',20)
    assert first['plan_id']==second['plan_id']
    statuses=dict((row['status'],row['total']) for row in first['sessions'])
    assert statuses['BLOCKED_INJURY']==1 and statuses['PLANNED']==1
    assert first['medical_bonus']==0.1
    assert service.maintenance_alerts(1)[0]['department']=='medicina'
    assert next(item for item in service.budget(1) if item['department']=='medicina')['next_level']==3
    report=service.individual_development(1)
    healthy = next(item for item in report if item['player_id'] == 10)
    assert healthy['performance_gap'] == 20
    service.close()
