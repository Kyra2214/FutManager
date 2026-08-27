from __future__ import annotations
from datetime import datetime, timezone
import json, sqlite3
from engine.core.state_store import assert_mutable_state_path

SCHEMA='''
CREATE TABLE IF NOT EXISTS gateway_mutation_audit(audit_id INTEGER PRIMARY KEY AUTOINCREMENT,career_id INTEGER,club_id INTEGER,action TEXT NOT NULL,idempotency_key TEXT NOT NULL,payload TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(action,idempotency_key));
CREATE INDEX IF NOT EXISTS idx_gateway_audit_scope ON gateway_mutation_audit(career_id,club_id,created_at DESC);
CREATE TABLE IF NOT EXISTS gateway_rpc_metrics(metric_id INTEGER PRIMARY KEY AUTOINCREMENT,action TEXT NOT NULL,duration_ms INTEGER NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS gateway_command_rollbacks(rollback_id INTEGER PRIMARY KEY AUTOINCREMENT,audit_id INTEGER NOT NULL,requested_by TEXT NOT NULL,reason TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(audit_id));
'''
CONTRACTS={
 'state_manifest': {'required': (), 'mutating': False},
 'career_start': {'required': ('managerName','targetType','targetId'), 'mutating': True},
 'finance_revenue': {'required': ('amount','reference'), 'mutating': True},
 'finance_summary': {'required': (), 'mutating': False},
 'events_list': {'required': (), 'mutating': False},
}

class GatewayContractService:
 def __init__(self,db):
  if not isinstance(db,sqlite3.Connection): assert_mutable_state_path(db)
  self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db; self.connection.row_factory=sqlite3.Row; self.connection.executescript(SCHEMA); self.connection.commit()
 def catalog(self): return [{'action':action,'required':list(spec['required']),'mutating':spec['mutating']} for action,spec in sorted(CONTRACTS.items())]
 def validate(self,action,payload):
  if action not in CONTRACTS: raise ValueError('GATEWAY_ACTION_UNKNOWN')
  if not isinstance(payload,dict): raise ValueError('GATEWAY_PAYLOAD_INVALID')
  missing=[key for key in CONTRACTS[action]['required'] if key not in payload or payload[key] in (None,'')]
  if missing: raise ValueError('GATEWAY_REQUIRED:'+missing[0])
  return {'action':action,'valid':True,'mutating':CONTRACTS[action]['mutating'],'payload':payload}
 def audit_mutation(self,action,payload,idempotency_key,career_id=None,club_id=None,status='APPLIED'):
  self.validate(action,payload)
  if not CONTRACTS[action]['mutating']: raise ValueError('GATEWAY_READ_ONLY')
  if not str(idempotency_key).strip(): raise ValueError('IDEMPOTENCY_KEY_REQUIRED')
  existing=self.connection.execute('SELECT * FROM gateway_mutation_audit WHERE action=? AND idempotency_key=?',(action,str(idempotency_key))).fetchone()
  if existing: return {'audit_id':int(existing['audit_id']),'status':existing['status'],'idempotent':True}
  with self.connection:
   cur=self.connection.execute('INSERT INTO gateway_mutation_audit(career_id,club_id,action,idempotency_key,payload,status,created_at) VALUES(?,?,?,?,?,?,?)',(career_id,club_id,action,str(idempotency_key),json.dumps(payload,sort_keys=True,ensure_ascii=False),status,datetime.now(timezone.utc).isoformat()))
  return {'audit_id':int(cur.lastrowid),'status':status,'idempotent':False}
 def validate_batch(self, action, payloads, max_items=50):
  if len(payloads) > int(max_items): raise ValueError('GATEWAY_BATCH_LIMIT')
  return [self.validate(action, payload) for payload in payloads]
 def record_rpc(self, action, duration_ms, status='OK'):
  if int(duration_ms)<0 or status not in ('OK','ERROR','TIMEOUT'): raise ValueError('RPC_METRIC_INVALID')
  with self.connection: cur=self.connection.execute('INSERT INTO gateway_rpc_metrics(action,duration_ms,status,created_at) VALUES(?,?,?,?)',(action,int(duration_ms),status,datetime.now(timezone.utc).isoformat()))
  return {'metric_id':int(cur.lastrowid),'action':action,'duration_ms':int(duration_ms),'status':status}
 def rollback(self, audit_id, requested_by, reason):
  row=self.connection.execute('SELECT * FROM gateway_mutation_audit WHERE audit_id=?',(int(audit_id),)).fetchone()
  if not row: raise KeyError(audit_id)
  with self.connection: self.connection.execute('INSERT OR IGNORE INTO gateway_command_rollbacks(audit_id,requested_by,reason,status,created_at) VALUES(?,?,?,?,?)',(int(audit_id),requested_by,reason,'REQUESTED',datetime.now(timezone.utc).isoformat()))
  return {'audit_id':int(audit_id),'status':'REQUESTED','data_mutation':False}
 def contract_version(self): return {'version':'701-1.0','utc':True,'source':'GameState'}

 def audit(self,career_id=None,club_id=None,action=None,limit=50):
  query='SELECT * FROM gateway_mutation_audit WHERE 1=1'; args=[]
  if career_id is not None: query+=' AND career_id=?'; args.append(career_id)
  if club_id is not None: query+=' AND club_id=?'; args.append(club_id)
  if action is not None: query+=' AND action=?'; args.append(action)
  rows=self.connection.execute(query+' ORDER BY audit_id DESC LIMIT ?',args+[min(max(int(limit),1),100)]).fetchall()
  return [dict(row) for row in rows]
 def close(self): self.connection.close()
