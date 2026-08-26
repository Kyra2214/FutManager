from __future__ import annotations
from enum import StrEnum
from datetime import date
import json,sqlite3
from engine.competitions.match_engine import CompetitionService
from engine.core.state_store import assert_mutable_state_path
class SimulationLevel(StrEnum): FULL='FULL'; STANDARD='STANDARD'; FAST='FAST'; ABSTRACT='ABSTRACT'
SCHEMA='''
CREATE TABLE IF NOT EXISTS simulation_ticks(simulation_tick_id TEXT PRIMARY KEY,logical_date TEXT NOT NULL,level TEXT NOT NULL,requested INTEGER NOT NULL,processed INTEGER NOT NULL DEFAULT 0,errors INTEGER NOT NULL DEFAULT 0,seed INTEGER,engine_version TEXT NOT NULL DEFAULT '1.0',status TEXT NOT NULL DEFAULT 'RUNNING',created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS simulation_audit(audit_id INTEGER PRIMARY KEY AUTOINCREMENT,simulation_tick_id TEXT NOT NULL,match_id INTEGER NOT NULL,level TEXT NOT NULL,seed INTEGER,result TEXT,processed_at TEXT NOT NULL,UNIQUE(simulation_tick_id,match_id));
CREATE INDEX IF NOT EXISTS idx_matches_pending on matches(status,match_date);
CREATE INDEX IF NOT EXISTS idx_sim_audit_tick on simulation_audit(simulation_tick_id);
'''
class WorldSimulationService:
 def __init__(self,db):
  assert_mutable_state_path(db) if not isinstance(db,sqlite3.Connection) else None;self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db;self.connection.row_factory=sqlite3.Row;self.connection.execute('PRAGMA foreign_keys=ON');self.connection.executescript(SCHEMA);self.connection.commit();self.matches=CompetitionService(self.connection)
 def simulate_batch(self,tick_id,level=SimulationLevel.ABSTRACT,batch_size=100,seed=0,priority_club_id=None,cancel_check=None):
  if self.connection.execute('select status from simulation_ticks where simulation_tick_id=?',(tick_id,)).fetchone(): return {'status':'ALREADY_PROCESSED','processed':self.connection.execute('select count(*) from simulation_audit where simulation_tick_id=?',(tick_id,)).fetchone()[0]}
  rows=self.connection.execute("select * from matches where status='SCHEDULED' order by match_date,match_id limit ?",(batch_size,)).fetchall();self.connection.execute('insert into simulation_ticks values(?,?,?,?,?,?,?,?,?,?)',(tick_id,date.today().isoformat(),level.value if hasattr(level,'value') else level,len(rows),0,0,seed,'1.0','RUNNING',date.today().isoformat())); self.connection.commit()
  processed=0
  try:
   for r in rows:
    if cancel_check is not None and cancel_check():
     self.connection.execute("update simulation_ticks set processed=?,status='CANCELLED' where simulation_tick_id=?",(processed,tick_id));self.connection.commit();return {'status':'CANCELLED','processed':processed}
    if priority_club_id and priority_club_id in (r['home_club_id'],r['away_club_id']): lvl=SimulationLevel.FULL
    else:lvl=level
    result=self.matches.play(r['match_id'],70,65,seed=seed+r['match_id']);self.connection.execute('insert into simulation_audit(simulation_tick_id,match_id,level,seed,result,processed_at) values(?,?,?,?,?,?)',(tick_id,r['match_id'],lvl.value,seed+r['match_id'],json.dumps({'home':result.home_goals,'away':result.away_goals}),date.today().isoformat())); self.connection.commit(); processed+=1
   self.connection.execute("update simulation_ticks set processed=?,status='COMPLETED' where simulation_tick_id=?",(processed,tick_id));self.connection.commit();return {'status':'COMPLETED','processed':processed}
  except Exception:
   self.connection.rollback();self.connection.execute("update simulation_ticks set errors=errors+1,status='ROLLED_BACK' where simulation_tick_id=?",(tick_id,));self.connection.commit();raise
 def close(self):self.matches.close()
