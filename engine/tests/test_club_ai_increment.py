import sqlite3
from engine.ai.club_ai import ClubAI


def db(tmp_path):
    path = tmp_path / 'ai.db'; con = sqlite3.connect(path)
    con.executescript('''
      CREATE TABLE times(time_id INTEGER PRIMARY KEY);
      CREATE TABLE jogadores(jogador_id INTEGER PRIMARY KEY,nome TEXT,idade INTEGER,cr1 INTEGER,cr2 INTEGER);
      CREATE TABLE jogador_time(jogador_id INTEGER,time_id INTEGER);
      CREATE TABLE player_sport_state(player_id INTEGER PRIMARY KEY,club_id INTEGER,category TEXT,available INTEGER,form INTEGER,condition INTEGER,fatigue INTEGER);
      CREATE TABLE club_economic_state(club_id INTEGER PRIMARY KEY,cash INTEGER,financial_status TEXT);
      INSERT INTO times VALUES(1); INSERT INTO club_economic_state VALUES(1,100000,'HEALTHY');
      INSERT INTO jogadores VALUES(10,'A',22,80,75); INSERT INTO jogador_time VALUES(10,1);
      INSERT INTO player_sport_state VALUES(10,1,'FIRST_TEAM',1,70,90,10);
    '''); con.commit(); con.close(); return path


def test_ai_weekly_is_idempotent_and_financially_conservative(tmp_path):
    ai = ClubAI(db(tmp_path)); ai.set_profile(1, salary_limit=200000, seed=4)
    first = ai.weekly_cycle(1, seed=99); second = ai.weekly_cycle(1, seed=99)
    assert first['idempotent'] is False and second['idempotent'] is True
    assert ai.propose_market(1, seed=100) == 'RECRUIT_SQUAD'
    objective = ai.add_objective(1, 'TOP4', priority=80)
    assert ai.update_objective(objective, 100)['status'] == 'COMPLETED'
    row = ai.connection.execute("SELECT alternatives FROM club_decision_history WHERE type='MARKET' ORDER BY decision_id DESC LIMIT 1").fetchone()
    assert 'HOLD_MARKET' in row[0]
    ai.close()


def test_ai_lineup_tactic_and_unknown_player_guard(tmp_path):
    path = db(tmp_path); con = sqlite3.connect(path)
    for player_id in range(20, 31):
        con.execute('INSERT INTO jogadores VALUES(?,?,?,?,?)', (player_id, f'P{player_id}', 24, 70, 70))
        con.execute('INSERT INTO jogador_time VALUES(?,1)', (player_id,))
        con.execute('INSERT INTO player_sport_state VALUES(?,?,?,?,?,?,?)', (player_id, 1, 'FIRST_TEAM', 1, 60, 90, 10))
    con.commit(); con.close()
    ai = ClubAI(path); ai.set_profile(1, strategy='AGGRESSIVE')
    lineup = ai.auto_lineup(1, seed=5); assert lineup['valid'] is True and len(lineup['player_ids']) == 11
    assert ai.choose_tactic(1, seed=5) == 'HIGH_PRESS'
    try:
        ai.propose_sale(1, 999, seed=5)
    except KeyError:
        pass
    else:
        raise AssertionError('atleta inexistente foi aceito pela IA')
    ai.close()


def test_ai_reputation_objective_and_diagnosis_benchmark(tmp_path):
    import time
    path = db(tmp_path); con = sqlite3.connect(path)
    con.execute('CREATE TABLE competitions(competition_id INTEGER PRIMARY KEY,name TEXT,status TEXT)')
    con.execute("INSERT INTO competitions VALUES(7,'Liga','ACTIVE')")
    con.execute('CREATE TABLE club_reputation(club_id INTEGER PRIMARY KEY,sporting REAL,national REAL,international REAL,commercial REAL,historical REAL)')
    con.execute('INSERT INTO club_reputation VALUES(1,80,70,60,50,40)'); con.commit(); con.close()
    ai = ClubAI(path); ai.add_objective(1, 'COMPETITION:7', priority=99)
    assert ai.prioritize_competitions(1, seed=2) == '[7]'
    context = ai.institutional_context(1); assert context['reputation'] == 60
    started = time.perf_counter()
    for _ in range(1000): ai.diagnose(1)
    assert time.perf_counter() - started < 3
    ai.close()
