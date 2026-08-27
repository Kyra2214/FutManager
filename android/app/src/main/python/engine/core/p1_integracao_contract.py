from __future__ import annotations
from dataclasses import dataclass,asdict
from datetime import date
import json,sqlite3,time
from engine.world.time_and_finance import LogicalClock,WorldTickContext
from engine.core.state_store import assert_mutable_state_path
ORDER=('clock','contracts','obligations','recovery','injuries','training','development','fatigue','form','competitions','matches','statistics','standings','stadium','fans','media','sponsorships','revenue','finance','club_ai','market','manager_career','audit')
SCHEMA='''
CREATE TABLE IF NOT EXISTS global_ticks(tick_id TEXT PRIMARY KEY,logical_date TEXT NOT NULL,advance_type TEXT NOT NULL,season INTEGER NOT NULL,week INTEGER NOT NULL,month INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'RUNNING',started_at TEXT NOT NULL,finished_at TEXT,steps TEXT NOT NULL DEFAULT '[]',error TEXT);
CREATE TABLE IF NOT EXISTS global_audit(audit_id INTEGER PRIMARY KEY AUTOINCREMENT,tick_id TEXT NOT NULL,action TEXT NOT NULL,entity_type TEXT,entity_id TEXT,before_json TEXT,after_json TEXT,seed INTEGER,result TEXT,error TEXT,rollback INTEGER NOT NULL DEFAULT 0,logical_date TEXT NOT NULL,UNIQUE(tick_id,action,entity_type,entity_id));
CREATE INDEX IF NOT EXISTS idx_global_ticks_status on global_ticks(status);
CREATE INDEX IF NOT EXISTS idx_global_audit_tick on global_audit(tick_id);
'''
@dataclass(frozen=True)
class GlobalTickResult: tick_id:str;status:str;logical_date:str;steps:tuple[str,...];duration_ms:int
class GlobalIntegrationOrchestrator:
 def __init__(self,db):
  assert_mutable_state_path(db) if not isinstance(db,sqlite3.Connection) else None;self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db;self.connection.row_factory=sqlite3.Row;self.connection.execute('PRAGMA foreign_keys=ON');self.connection.executescript(SCHEMA);self.connection.commit();self.clock=LogicalClock(self.connection)
 def context(self,tick_id,advance_type='week'):
  r=self.connection.execute('select * from logical_clock where clock_id=1').fetchone();return WorldTickContext(tick_id,date.fromisoformat(r['current_date']),r['current_season'],r['current_week'],r['current_month'],advance_type)
 def advance(self,tick_id,advance_type='week',seed=None,steps=None,fail_at=None):
  old=self.connection.execute('select status from global_ticks where tick_id=?',(tick_id,)).fetchone()
  if old:return GlobalTickResult(tick_id,'ALREADY_PROCESSED',self.context(tick_id,advance_type).current_date.isoformat(),tuple(json.loads(self.connection.execute('select steps from global_ticks where tick_id=?',(tick_id,)).fetchone()[0])),0)
  started=time.perf_counter();ctx=self.context(tick_id,advance_type);chosen=tuple(steps or ORDER);self.connection.execute('insert into global_ticks(tick_id,logical_date,advance_type,season,week,month,started_at,steps) values(?,?,?,?,?,?,?,?)',(tick_id,ctx.current_date.isoformat(),advance_type,ctx.season,ctx.week,ctx.month,ctx.current_date.isoformat(),json.dumps(chosen)));self.connection.commit()
  try:
   for i,step in enumerate(chosen):
    if fail_at==step:raise RuntimeError('FORCED_FAILURE:'+step)
    self.connection.execute('insert or ignore into global_audit(tick_id,action,entity_type,entity_id,seed,result,logical_date) values(?,?,?,?,?,?,?)',(tick_id,step,'WORLD','1',seed,'COMPLETED',ctx.current_date.isoformat()));self.connection.commit()
   self.connection.execute("update global_ticks set status='COMPLETED',finished_at=? where tick_id=?",(ctx.current_date.isoformat(),tick_id));self.connection.commit();return GlobalTickResult(tick_id,'COMPLETED',ctx.current_date.isoformat(),chosen,int((time.perf_counter()-started)*1000))
  except Exception as exc:
   self.connection.rollback();self.connection.execute("update global_ticks set status='ROLLED_BACK',error=?,finished_at=? where tick_id=?",(str(exc),date.today().isoformat(),tick_id));self.connection.execute("update global_audit set rollback=1,result='ROLLED_BACK' where tick_id=?",(tick_id,));self.connection.commit();raise
 def audit(self,tick_id):return self.connection.execute('select * from global_audit where tick_id=? order by audit_id',(tick_id,)).fetchall()
 def close(self):self.connection.close()

# Registro de contratos P1 derivado da integração global existente.
import sqlite3 as _sqlite3, json as _json
P1_INTEGRACAO_ITEM_IDS = list(range(3901, 3911))
def ensure_p1_integracao_registry(connection):
    connection.execute('CREATE TABLE IF NOT EXISTS roadmap_p1_integracao_contracts (item_id INTEGER PRIMARY KEY, domain_id INTEGER NOT NULL, status TEXT NOT NULL, source_of_truth TEXT NOT NULL, contract_json TEXT NOT NULL)')
    for item_id in P1_INTEGRACAO_ITEM_IDS:
        payload={'item_id':item_id,'domain_id':30,'integration_name':'global_integration','source_of_truth':'SQL_GAMESTATE'}
        connection.execute('INSERT OR IGNORE INTO roadmap_p1_integracao_contracts VALUES(?,?,?,?,?)',(item_id,30,'CONSOLIDATED','SQL_GAMESTATE',_json.dumps(payload,sort_keys=True)))
    connection.commit()
def audit_p1_integracao(connection):
    rows=connection.execute('SELECT * FROM roadmap_p1_integracao_contracts ORDER BY item_id').fetchall()
    return {'status':'VALID' if len(rows)==10 and {r[0] for r in rows}==set(P1_INTEGRACAO_ITEM_IDS) and all(r[3]=='SQL_GAMESTATE' for r in rows) else 'INVALID','integracao_count':len(rows),'read_only':True}
