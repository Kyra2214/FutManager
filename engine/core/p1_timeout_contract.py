from __future__ import annotations
import hashlib,json,sqlite3
from datetime import datetime,timezone
from engine.core.domain_errors import DomainError,DomainErrorCode
ITEM_IDS=tuple(range(1101,1111)); ACTIONS=('DEFINE_CONTRACT','VALIDATE_RULES','PERSIST_STATE','EXPOSE_READ','PROTECT_MUTATION','AUDIT_FLOW','OPTIMIZE_QUERY','SIMULATE_SCENARIO','DOCUMENT_CYCLE','TEST_INTEGRATION')
def _now(): return datetime.now(timezone.utc).isoformat()
def ensure_p1_timeout_registry(c):
 c.executescript('''CREATE TABLE IF NOT EXISTS roadmap_p1_timeouts(item_id INTEGER PRIMARY KEY,domain_id INTEGER NOT NULL,timeout_name TEXT NOT NULL,timeout_ms INTEGER NOT NULL,action TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'CONSOLIDATED',source_of_truth TEXT NOT NULL DEFAULT 'SQL_GAMESTATE',contract_json TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL); CREATE TABLE IF NOT EXISTS roadmap_p1_timeout_audit(audit_id INTEGER PRIMARY KEY AUTOINCREMENT,item_id INTEGER NOT NULL,action TEXT NOT NULL,allowed INTEGER NOT NULL,reason TEXT NOT NULL,payload TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(item_id,action)); CREATE INDEX IF NOT EXISTS idx_p1_timeout_lookup ON roadmap_p1_timeouts(timeout_name,action,status);''')
 n=_now()
 for i,a in zip(ITEM_IDS,ACTIONS):
  x={'item_id':i,'domain_id':2,'timeout_name':'career_gateway','timeout_ms':30000,'action':a,'source_of_truth':'SQL_GAMESTATE','schema_version':1}; c.execute('INSERT OR IGNORE INTO roadmap_p1_timeouts VALUES(?,?,?,?,?,?,?,?,?,?)',(i,2,'career_gateway',30000,a,'CONSOLIDATED','SQL_GAMESTATE',json.dumps(x,sort_keys=True,separators=(',',':')),n,n))
 c.commit()
def validate_p1_timeout(c,i):
 r=c.execute('SELECT * FROM roadmap_p1_timeouts WHERE item_id=?',(i,)).fetchone()
 if r is None: raise ValueError('P1_TIMEOUT_NOT_FOUND')
 x=json.loads(r['contract_json']); checks={'item_id':x.get('item_id')==i,'domain_id':x.get('domain_id')==2,'timeout_name':x.get('timeout_name')=='career_gateway','timeout_ms':isinstance(x.get('timeout_ms'),int) and x.get('timeout_ms')>0,'action':x.get('action') in ACTIONS,'source_of_truth':x.get('source_of_truth')=='SQL_GAMESTATE'}; return {'status':'VALID' if all(checks.values()) else 'INVALID','item_id':i,'checks':checks,'contract':x,'read_only':True}
def read_p1_timeouts(c): return [{**dict(r),'contract_json':json.loads(r['contract_json'])} for r in c.execute('SELECT * FROM roadmap_p1_timeouts ORDER BY item_id')]
def audit_p1_timeouts(c):
 r=read_p1_timeouts(c); bad=[x['item_id'] for x in r if validate_p1_timeout(c,x['item_id'])['status']!='VALID']; checks={'count_10':len(r)==10,'expected_ids':{x['item_id'] for x in r}==set(ITEM_IDS),'all_consolidated':all(x['status']=='CONSOLIDATED' for x in r),'sql_game_state':all(x['source_of_truth']=='SQL_GAMESTATE' for x in r),'valid_contracts':not bad}; return {'status':'VALID' if all(checks.values()) else 'INVALID','timeout_count':len(r),'checks':checks,'invalid_items':bad,'read_only':True}
def protect_p1_timeout_mutation(c,i,actor,payload):
 v=validate_p1_timeout(c,i); ok=actor=='AUTHORIZED_SQL_SERVICE' and v['status']=='VALID'; s=json.dumps(payload,sort_keys=True,separators=(',',':')); c.execute('INSERT OR REPLACE INTO roadmap_p1_timeout_audit(item_id,action,allowed,reason,payload,created_at) VALUES(?,?,?,?,?,?)',(i,'PROTECT_MUTATION',int(ok),'ALLOWED' if ok else 'SQL_SERVICE_AUTHORIZATION_REQUIRED',s,_now())); c.commit()
 if not ok: raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
 return {'allowed':True,'item_id':i,'payload_hash':hashlib.sha256(s.encode()).hexdigest()}
