import sqlite3
from engine.ai.club_ai import ClubAI

def test_ai_decision_approval_and_audit(tmp_path):
    path = tmp_path / 'ai-p1.db'
    con = sqlite3.connect(path)
    con.executescript('''
      CREATE TABLE jogadores(jogador_id INTEGER PRIMARY KEY,nome TEXT,idade INTEGER,cr1 INTEGER,cr2 INTEGER);
      CREATE TABLE jogador_time(jogador_id INTEGER,time_id INTEGER);
      CREATE TABLE player_sport_state(player_id INTEGER PRIMARY KEY,club_id INTEGER,category TEXT,available INTEGER,form INTEGER,condition INTEGER,fatigue INTEGER);
      CREATE TABLE club_economic_state(club_id INTEGER PRIMARY KEY,cash INTEGER,financial_status TEXT);
      INSERT INTO club_economic_state VALUES(1,100000,'HEALTHY');
    ''')
    con.commit(); con.close()
    ai = ClubAI(path)
    ai.set_profile(1, seed=7)
    ai.propose_market(1, seed=10)
    decision = ai.connection.execute('SELECT decision_id FROM club_decision_history ORDER BY decision_id DESC LIMIT 1').fetchone()[0]
    approved = ai.approve_decision(decision, 'manager')
    assert approved['status'] == 'APPROVED'
    audit = ai.decision_audit(1, seed=10)
    assert audit['count'] == 1 and audit['decisions'][0]['approval_status'] == 'APPROVED'
    ai.set_risk_limit(1, 2026, 1000)
    preview = ai.strategic_preview(1, 2026, 'GROWTH', 500)
    assert preview['persisted'] is False and preview['incompatible'] is False
    approved_strategy = ai.approve_strategy(1, 2026, 'GROWTH', 500)
    assert approved_strategy['status'] == 'APPROVED'
    explanation = ai.explain_diagnosis(1)
    assert {fact['source'] for fact in explanation['facts']} == {'player_sport_state', 'club_economic_state'}
    ai.close()
