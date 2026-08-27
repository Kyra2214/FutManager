import sqlite3
from engine.world.simulation import WorldSimulationService, SimulationLevel

def test_world_simulation_batch_checkpoint_metrics_and_resume():
    c=sqlite3.connect(':memory:')
    c.execute('CREATE TABLE matches(match_id INTEGER PRIMARY KEY,competition_id INTEGER,season_id INTEGER NOT NULL,match_date TEXT NOT NULL,round INTEGER NOT NULL,home_club_id INTEGER NOT NULL,away_club_id INTEGER NOT NULL,home_lineup_id INTEGER,away_lineup_id INTEGER,home_goals INTEGER,away_goals INTEGER,status TEXT NOT NULL,seed INTEGER,home_form INTEGER NOT NULL DEFAULT 0,away_form INTEGER NOT NULL DEFAULT 0,home_morale INTEGER NOT NULL DEFAULT 0,away_morale INTEGER NOT NULL DEFAULT 0,home_tactic INTEGER NOT NULL DEFAULT 0,away_tactic INTEGER NOT NULL DEFAULT 0)')
    c.execute("INSERT INTO matches(match_id,competition_id,season_id,match_date,round,home_club_id,away_club_id,status) VALUES(1,10,2027,'2027-01-01',1,1,2,'SCHEDULED')")
    c.execute("INSERT INTO matches(match_id,competition_id,season_id,match_date,round,home_club_id,away_club_id,status) VALUES(2,10,2027,'2027-01-08',2,2,3,'SCHEDULED')")
    service=WorldSimulationService(c)
    result=service.simulate_batch('sim-1',SimulationLevel.ABSTRACT,2,42)
    assert result['status']=='COMPLETED' and result['processed']==2
    metrics=service.batch_metrics('sim-1')
    assert metrics['processed']==2 and metrics['checkpoints']==2
    assert service.resume('sim-1')['status']=='ALREADY_COMPLETED'
    assert service.failure_report('sim-1')['persisted'] is True
    service.close()
