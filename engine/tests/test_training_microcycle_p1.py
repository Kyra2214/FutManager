import sqlite3
from engine.sports.training import TrainingService

def test_training_microcycle_overtraining_and_audit():
    c=sqlite3.connect(':memory:')
    c.execute('CREATE TABLE times(time_id INTEGER PRIMARY KEY)'); c.execute('INSERT INTO times VALUES(1)')
    c.execute('CREATE TABLE jogadores(jogador_id INTEGER PRIMARY KEY,nome TEXT,cr2 INTEGER)'); c.execute("INSERT INTO jogadores VALUES(10,'Atleta',80)")
    c.execute('CREATE TABLE jogador_time(jogador_id INTEGER,time_id INTEGER)'); c.execute('INSERT INTO jogador_time VALUES(10,1)')
    c.execute('CREATE TABLE player_sport_state(player_id INTEGER PRIMARY KEY,condition INTEGER,fatigue INTEGER)'); c.execute('INSERT INTO player_sport_state VALUES(10,100,0)')
    c.execute('CREATE TABLE injuries(player_id INTEGER,status TEXT)')
    c.execute('CREATE TABLE staff_members(staff_id INTEGER PRIMARY KEY,club_id INTEGER,level INTEGER,status TEXT,role TEXT)')
    service=TrainingService(c)
    micro=service.create_microcycle(1,2027,1,'TACTICAL',80,2)
    assert micro['intensity']==80
    plan=service.create_weekly_plan(1,2027,1,'PHYSICAL',90)
    assert service.overtraining_report(1,2027,1)['risk']=='HIGH'
    assert service.training_audit(1,plan['plan_id'])[0]['action']=='CREATE'
    assert service.approve_plan(plan['plan_id'])['status']=='APPROVED'
    assert service.cancel_plan(plan['plan_id'])['status']=='CANCELLED'
    service.close()
