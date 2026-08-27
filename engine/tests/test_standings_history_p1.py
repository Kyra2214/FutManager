from __future__ import annotations

import sqlite3

from engine.competitions.structure import CompetitionStructureService


def test_standings_snapshot_history_and_reconciliation():
    con = sqlite3.connect(':memory:')
    con.executescript('CREATE TABLE competitions(competition_id INTEGER PRIMARY KEY,name TEXT,season_id INTEGER,type TEXT,club_count INTEGER,format TEXT,status TEXT DEFAULT \'ACTIVE\'); CREATE TABLE team_competition_stats(competition_id INTEGER,club_id INTEGER,played INTEGER DEFAULT 0,wins INTEGER DEFAULT 0,draws INTEGER DEFAULT 0,losses INTEGER DEFAULT 0,goals_for INTEGER DEFAULT 0,goals_against INTEGER DEFAULT 0,points INTEGER DEFAULT 0,PRIMARY KEY(competition_id,club_id));')
    service = CompetitionStructureService(con)
    con = service.connection
    con.execute("INSERT INTO competitions(competition_id,name,season_id,type,club_count,format) VALUES(1,'Liga',1,'LEAGUE',2,'TABLE')")
    con.execute("INSERT INTO team_competition_stats(competition_id,club_id,played,wins,goals_for,goals_against,points) VALUES(1,10,1,1,3,0,3),(1,20,1,0,0,3,0)")
    con.commit()
    assert service.snapshot_standings(1) == 2
    assert service.historical_standings(1, 1)[0]['club_id'] == 10
    assert service.reconcile_standings(1)['reconciled'] is True
    service.close()
