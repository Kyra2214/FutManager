import sqlite3
from engine.sports.health import HealthService

def test_health_return_protocol_selection_treatment_and_audit():
    c=sqlite3.connect(':memory:')
    c.execute('CREATE TABLE times(time_id INTEGER PRIMARY KEY)'); c.execute('INSERT INTO times VALUES(1)')
    c.execute('CREATE TABLE jogadores(jogador_id INTEGER PRIMARY KEY,nome TEXT,idade INTEGER)'); c.execute("INSERT INTO jogadores VALUES(10,'Atleta',24)")
    c.execute('CREATE TABLE jogador_time(jogador_id INTEGER,time_id INTEGER)'); c.execute('INSERT INTO jogador_time VALUES(10,1)')
    c.execute('CREATE TABLE player_sport_state(player_id INTEGER PRIMARY KEY,available INTEGER,current_injury_id INTEGER,recovery_days INTEGER,last_updated TEXT,condition INTEGER)'); c.execute('INSERT INTO player_sport_state VALUES(10,1,NULL,0,"2027-01-01",100)')
    c.execute('CREATE TABLE injuries(injury_id INTEGER PRIMARY KEY AUTOINCREMENT,player_id INTEGER,injury_type TEXT,start_date TEXT,estimated_days INTEGER,end_date TEXT,severity TEXT,status TEXT)')
    service=HealthService(c)
    protocol=service.set_return_protocol(1,10,30,.4,'LIMITED')
    assert protocol['minutes_limit']==30
    assert service.selection_eligibility(1,10)['eligible'] is False
    treatment=service.apply_treatment(1,10,'PHYSIO',1000,3,'treat-1')
    assert treatment['status']=='APPLIED' and service.apply_treatment(1,10,'PHYSIO',1000,3,'treat-1')['treatment_id']==treatment['treatment_id']
    assert service.clinical_audit(1,10)['persisted'] is True
    service.close()
