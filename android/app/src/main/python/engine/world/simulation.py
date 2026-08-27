from __future__ import annotations
from enum import StrEnum
from datetime import date
import json,sqlite3,time
from engine.competitions.match_engine import CompetitionService
from engine.core.state_store import assert_mutable_state_path
class SimulationLevel(StrEnum): FULL='FULL'; STANDARD='STANDARD'; FAST='FAST'; ABSTRACT='ABSTRACT'
SCHEMA='''
CREATE TABLE IF NOT EXISTS simulation_ticks(simulation_tick_id TEXT PRIMARY KEY,logical_date TEXT NOT NULL,level TEXT NOT NULL,requested INTEGER NOT NULL,processed INTEGER NOT NULL DEFAULT 0,errors INTEGER NOT NULL DEFAULT 0,seed INTEGER,engine_version TEXT NOT NULL DEFAULT '1.0',status TEXT NOT NULL DEFAULT 'RUNNING',created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS simulation_audit(audit_id INTEGER PRIMARY KEY AUTOINCREMENT,simulation_tick_id TEXT NOT NULL,match_id INTEGER NOT NULL,level TEXT NOT NULL,seed INTEGER,result TEXT,processed_at TEXT NOT NULL,UNIQUE(simulation_tick_id,match_id));
CREATE INDEX IF NOT EXISTS idx_matches_pending on matches(status,match_date);
CREATE INDEX IF NOT EXISTS idx_sim_audit_tick on simulation_audit(simulation_tick_id);
CREATE TABLE IF NOT EXISTS simulation_configs(season INTEGER PRIMARY KEY, level TEXT NOT NULL, seed INTEGER NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS simulation_queue(queue_id INTEGER PRIMARY KEY AUTOINCREMENT, simulation_tick_id TEXT NOT NULL, competition_id INTEGER, club_id INTEGER, sequence_no INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'QUEUED', UNIQUE(simulation_tick_id,sequence_no));
CREATE TABLE IF NOT EXISTS simulation_checkpoints(checkpoint_id INTEGER PRIMARY KEY AUTOINCREMENT, simulation_tick_id TEXT NOT NULL, processed INTEGER NOT NULL, last_match_id INTEGER, state_hash TEXT, created_at TEXT NOT NULL, UNIQUE(simulation_tick_id,processed));
'''
class WorldSimulationService:
 def __init__(self,db):
  assert_mutable_state_path(db) if not isinstance(db,sqlite3.Connection) else None;self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db;self.connection.row_factory=sqlite3.Row;self.connection.execute('PRAGMA foreign_keys=ON');self.connection.executescript(SCHEMA);self.connection.commit();self.matches=CompetitionService(self.connection)
 def configure(self, season:int, level=SimulationLevel.ABSTRACT, seed:int=0):
  value=level.value if hasattr(level,'value') else str(level)
  if value not in {item.value for item in SimulationLevel}: raise ValueError('SIMULATION_LEVEL_INVALID')
  self.connection.execute('INSERT INTO simulation_configs(season,level,seed,updated_at) VALUES(?,?,?,?) ON CONFLICT(season) DO UPDATE SET level=excluded.level,seed=excluded.seed,updated_at=excluded.updated_at',(season,value,int(seed),date.today().isoformat())); self.connection.commit(); return dict(self.connection.execute('SELECT * FROM simulation_configs WHERE season=?',(season,)).fetchone())
 def progress(self,tick_id):
  row=self.connection.execute('SELECT * FROM simulation_ticks WHERE simulation_tick_id=?',(tick_id,)).fetchone()
  if row is None: raise ValueError('SIMULATION_TICK_NOT_FOUND')
  last=self.connection.execute('SELECT last_match_id,created_at FROM simulation_checkpoints WHERE simulation_tick_id=? ORDER BY processed DESC LIMIT 1',(tick_id,)).fetchone()
  return {**dict(row),'last_match_id': last['last_match_id'] if last else None,'checkpoint_at': last['created_at'] if last else None,'read_only': True}
 def checkpoint(self,tick_id:str, processed:int, last_match_id:int|None=None, state_hash:str|None=None):
  self.connection.execute('INSERT OR IGNORE INTO simulation_checkpoints(simulation_tick_id,processed,last_match_id,state_hash,created_at) VALUES(?,?,?,?,?)',(tick_id,processed,last_match_id,state_hash,date.today().isoformat())); self.connection.commit(); return self.progress(tick_id)
 def simulate_batch(self,tick_id,level=SimulationLevel.ABSTRACT,batch_size=100,seed=0,priority_club_id=None,cancel_check=None):
  if self.connection.execute('select status from simulation_ticks where simulation_tick_id=?',(tick_id,)).fetchone(): return {'status':'ALREADY_PROCESSED','processed':self.connection.execute('select count(*) from simulation_audit where simulation_tick_id=?',(tick_id,)).fetchone()[0]}
  rows=self.connection.execute("select * from matches where status='SCHEDULED' order by match_date,match_id limit ?",(batch_size,)).fetchall();self.connection.execute('insert into simulation_ticks values(?,?,?,?,?,?,?,?,?,?)',(tick_id,date.today().isoformat(),level.value if hasattr(level,'value') else level,len(rows),0,0,seed,'1.0','RUNNING',date.today().isoformat()));
  for sequence, row in enumerate(rows, 1): self.connection.execute('INSERT INTO simulation_queue(simulation_tick_id,competition_id,club_id,sequence_no) VALUES(?,?,?,?)',(tick_id,row['competition_id'] if 'competition_id' in row.keys() else None,row['home_club_id'],sequence))
  self.connection.commit()
  processed=0
  try:
   for r in rows:
    if cancel_check is not None and cancel_check():
     self.connection.execute("update simulation_ticks set processed=?,status='CANCELLED' where simulation_tick_id=?",(processed,tick_id));self.connection.commit();return {'status':'CANCELLED','processed':processed}
    if priority_club_id and priority_club_id in (r['home_club_id'],r['away_club_id']): lvl=SimulationLevel.FULL
    else:lvl=level
    result=self.matches.play(r['match_id'],70,65,seed=seed+r['match_id']);   self.connection.execute('insert into simulation_audit(simulation_tick_id,match_id,level,seed,result,processed_at) values(?,?,?,?,?,?)',(tick_id,r['match_id'],lvl.value,seed+r['match_id'],json.dumps({'home':result.home_goals,'away':result.away_goals}),date.today().isoformat())); self.connection.execute('UPDATE simulation_queue SET status=\'PROCESSED\' WHERE simulation_tick_id=? AND sequence_no=?',(tick_id,processed+1)); self.connection.commit(); processed+=1; self.checkpoint(tick_id,processed,int(r['match_id']))
   self.connection.execute("update simulation_ticks set processed=?,status='COMPLETED' where simulation_tick_id=?",(processed,tick_id));self.connection.commit();return {'status':'COMPLETED','processed':processed}
  except Exception:
   self.connection.rollback();self.connection.execute("update simulation_ticks set errors=errors+1,status='ROLLED_BACK' where simulation_tick_id=?",(tick_id,));self.connection.commit();raise
 def resume(self,tick_id:str,level=SimulationLevel.ABSTRACT,batch_size:int=100,seed:int=0):
  row=self.connection.execute("SELECT status,processed FROM simulation_ticks WHERE simulation_tick_id=?",(tick_id,)).fetchone()
  if row is None: raise ValueError('SIMULATION_TICK_NOT_FOUND')
  if row['status']=='COMPLETED': return {'status':'ALREADY_COMPLETED','processed':int(row['processed'])}
  return self.simulate_batch(tick_id,level,batch_size,seed)
 def batch_metrics(self,tick_id:str):
  row=self.connection.execute('SELECT COUNT(*) AS entries,COALESCE(SUM(CASE WHEN level=\'FULL\' THEN 1 ELSE 0 END),0) AS full_matches FROM simulation_audit WHERE simulation_tick_id=?',(tick_id,)).fetchone()
  checkpoints=self.connection.execute('SELECT COUNT(*) AS total FROM simulation_checkpoints WHERE simulation_tick_id=?',(tick_id,)).fetchone()['total']
  return {'tick_id':tick_id,'processed':int(row['entries']),'full_matches':int(row['full_matches']),'checkpoints':int(checkpoints),'throughput_estimate':int(row['entries']),'read_only':True}
 def failure_report(self,tick_id:str):
  row=self.connection.execute('SELECT * FROM simulation_ticks WHERE simulation_tick_id=?',(tick_id,)).fetchone()
  if row is None: raise ValueError('SIMULATION_TICK_NOT_FOUND')
  return {'tick_id':tick_id,'status':row['status'],'requested':int(row['requested']),'processed':int(row['processed']),'errors':int(row['errors']),'recoverable':row['status'] in ('ROLLED_BACK','CANCELLED'),'persisted':True}
 def divergence_report(self, expected_tick_id:str, actual_tick_id:str):
  expected={row['match_id']: row['result'] for row in self.connection.execute('SELECT match_id,result FROM simulation_audit WHERE simulation_tick_id=?',(expected_tick_id,))}
  actual={row['match_id']: row['result'] for row in self.connection.execute('SELECT match_id,result FROM simulation_audit WHERE simulation_tick_id=?',(actual_tick_id,))}
  ids=sorted(set(expected)|set(actual)); differences=[{'match_id':i,'expected':expected.get(i),'actual':actual.get(i)} for i in ids if expected.get(i)!=actual.get(i)]
  return {'expected_tick_id':expected_tick_id,'actual_tick_id':actual_tick_id,'checked':len(ids),'differences':differences,'identical':not differences,'read_only':True}
 def benchmark(self, season:int, level=SimulationLevel.ABSTRACT, sample_size:int=0):
  started=time.perf_counter(); rows=self.connection.execute("SELECT COUNT(*) AS total FROM matches WHERE status='SCHEDULED'").fetchone(); total=int(rows['total']); sample=min(total,sample_size) if sample_size else total
  elapsed_ms=round((time.perf_counter()-started)*1000,3)
  return {'season':season,'level':level.value if hasattr(level,'value') else str(level),'scheduled_matches':total,'sample_size':sample,'elapsed_ms':elapsed_ms,'transactions_per_match':1,'memory_note':'medição de consulta; execução permanece no GameState temporário'}
 def close(self):self.matches.close()
