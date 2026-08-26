import sqlite3
from engine.sports.health import HealthService


def fixture(tmp_path):
    path = tmp_path / "health.db"
    con = sqlite3.connect(path)
    con.executescript('''
      CREATE TABLE times(time_id INTEGER PRIMARY KEY);
      CREATE TABLE jogadores(jogador_id INTEGER PRIMARY KEY,nome TEXT,idade INTEGER);
      CREATE TABLE jogador_time(jogador_id INTEGER,time_id INTEGER);
      CREATE TABLE player_sport_state(player_id INTEGER PRIMARY KEY,available INTEGER,current_injury_id INTEGER,recovery_days INTEGER,last_updated TEXT,condition INTEGER);
      CREATE TABLE injuries(injury_id INTEGER PRIMARY KEY AUTOINCREMENT,player_id INTEGER,injury_type TEXT,start_date TEXT,estimated_days INTEGER,end_date TEXT,severity TEXT,status TEXT);
      CREATE TABLE player_suspensions(player_id INTEGER PRIMARY KEY,until_date TEXT,reason TEXT,active INTEGER,created_at TEXT);
      CREATE TABLE staff_members(staff_id INTEGER PRIMARY KEY,club_id INTEGER,role TEXT,level INTEGER,status TEXT);
      INSERT INTO times VALUES(1);
      INSERT INTO jogadores VALUES(10,'Atleta Saúde',25);
      INSERT INTO jogador_time VALUES(10,1);
      INSERT INTO player_sport_state VALUES(10,1,NULL,0,'2026-01-01',100);
      INSERT INTO staff_members VALUES(1,1,'medico',5,'ativo');
    ''')
    con.commit(); con.close(); return path


def test_health_cycle_alerts_filters_and_suspension(tmp_path):
    service = HealthService(fixture(tmp_path))
    injury = service.register_injury(1, 10, 'distensão', 'MODERATE', 2026, 1, seed=7)
    assert injury['estimated_days'] > 0
    assert service.list_health(1, severity='MODERATE', max_days=30)[0]['player_id'] == 10
    assert service.alerts(1)[0]['alert_type'] == 'NEW_INJURY'
    progress = service.recover(1, days=1)
    assert progress[0]['remaining_days'] < injury['estimated_days']
    suspension = service.register_suspension(1, 10, cards=2, red_card=False, season=2026, week=1)
    assert suspension['matches'] == 2
    try:
        service.register_injury(1, 99, 'x', 'MINOR', 2026, 1)
    except ValueError as error:
        assert str(error) == 'PLAYER_OUTSIDE_CLUB'
    else:
        raise AssertionError('jogador fora do clube não foi rejeitado')
    service.close()
