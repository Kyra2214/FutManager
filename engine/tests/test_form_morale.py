import sqlite3
from engine.sports.form_morale import FormMoraleService


def fixture(tmp_path):
    path=tmp_path/'form.db'; con=sqlite3.connect(path)
    con.executescript('''
      CREATE TABLE times(time_id INTEGER PRIMARY KEY);
      CREATE TABLE jogadores(jogador_id INTEGER PRIMARY KEY,nome TEXT,cr2 INTEGER,idade INTEGER);
      CREATE TABLE jogador_time(jogador_id INTEGER,time_id INTEGER);
      CREATE TABLE player_sport_state(player_id INTEGER PRIMARY KEY,form INTEGER,fatigue INTEGER,condition INTEGER,last_updated TEXT);
      INSERT INTO times VALUES(1);
      INSERT INTO jogadores VALUES(10,'Atleta A',80,25),(11,'Atleta B',75,36);
      INSERT INTO jogador_time VALUES(10,1),(11,1);
      INSERT INTO player_sport_state VALUES(10,50,20,100,'2026-01-01'),(11,40,80,50,'2026-01-01');
    '''); con.commit(); con.close(); return path


def test_form_morale_is_seeded_and_rest_is_recommended(tmp_path):
    service=FormMoraleService(fixture(tmp_path))
    first=service.update_after_match(1,'WIN',2026,1,77)
    second=service.update_after_match(1,'WIN',2026,2,77)
    assert first['average'] > 50 and second['average'] > first['average']
    training=service.apply_weekly_training(1,2026,3,'PHYSICAL',90,seed=11,international_matches=1)
    assert training['changes'][1]['effective_load'] < training['changes'][0]['effective_load']
    rest=service.apply_weekly_training(1,2026,4,'REST',90,seed=11)
    assert all(change['fatigue_delta'] < 0 for change in rest['changes'])
    prep=service.create_opponent_preparation(1,2,2026,5,'bloquear transição')
    assert prep['focus']=='bloquear transição'
    assert any(item['type']=='REST' for item in service.recommendations(1))
    service.close()
