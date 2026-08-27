from __future__ import annotations
import hashlib,json,sqlite3
from datetime import datetime,timezone
from engine.core.domain_errors import DomainError,DomainErrorCode
ITEM_IDS=tuple(range(1201,1211)); ACTIONS=("DEFINE_CONTRACT","VALIDATE_RULES","PERSIST_STATE","EXPOSE_READ","PROTECT_MUTATION","AUDIT_FLOW","OPTIMIZE_QUERY","SIMULATE_SCENARIO","DOCUMENT_CYCLE","TEST_INTEGRATION")
def _now(): return datetime.now(timezone.utc).isoformat()
def ensure_p1_mfa_registry(c):
 c.executescript("""CREATE TABLE IF NOT EXISTS roadmap_p1_mfa_contracts(item_id INTEGER PRIMARY KEY,domain_id INTEGER NOT NULL,mfa_name TEXT NOT NULL,payload_schema TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'CONSOLIDATED',source_of_truth TEXT NOT NULL DEFAULT 'SQL_GAMESTATE',contract_json TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS roadmap_p1_mfa_states(mfa_key TEXT PRIMARY KEY,career_id INTEGER,subject_id INTEGER,method TEXT NOT NULL,status TEXT NOT NULL,payload_json TEXT NOT NULL,payload_hash TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS roadmap_p1_mfa_audit(audit_id INTEGER PRIMARY KEY AUTOINCREMENT,item_id INTEGER NOT NULL,action TEXT NOT NULL,allowed INTEGER NOT NULL,reason TEXT NOT NULL,payload TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(item_id,action));CREATE INDEX IF NOT EXISTS idx_p1_mfa_lookup ON roadmap_p1_mfa_states(career_id,subject_id,status,updated_at);""")
 n=_now()
 for i,a in zip(ITEM_IDS,ACTIONS):
  x={'item_id':i,'domain_id':3,'mfa_name':'career_mfa','payload_schema':'mfa_key,career_id,subject_id,method,status,payload','action':a,'source_of_truth':'SQL_GAMESTATE','schema_version':1}; c.execute('INSERT OR IGNORE INTO roadmap_p1_mfa_contracts VALUES(?,?,?,?,?,?,?,?,?)',(i,3,'career_mfa',x['payload_schema'],'CONSOLIDATED','SQL_GAMESTATE',json.dumps(x,sort_keys=True,separators=(',',':')),n,n))
 c.commit()
def validate_p1_mfa(c,i):
 r=c.execute('SELECT * FROM roadmap_p1_mfa_contracts WHERE item_id=?',(i,)).fetchone()
 if r is None: raise ValueError('P1_MFA_NOT_FOUND')
 x=json.loads(r['contract_json']); checks={'item_id':x.get('item_id')==i,'domain_id':x.get('domain_id')==3,'mfa_name':x.get('mfa_name')=='career_mfa','action':x.get('action') in ACTIONS,'source_of_truth':x.get('source_of_truth')=='SQL_GAMESTATE'}; return {'status':'VALID' if all(checks.values()) else 'INVALID','item_id':i,'checks':checks,'contract':x,'read_only':True}
def read_p1_mfas(c): return [{**dict(r),'contract_json':json.loads(r['contract_json'])} for r in c.execute('SELECT * FROM roadmap_p1_mfa_contracts ORDER BY item_id')]
def persist_p1_mfa(c,key,payload,career_id=None,subject_id=None,method='TOTP',status='ENABLED',actor=''):
 if actor!='AUTHORIZED_SQL_SERVICE': raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
 if not key.strip() or method not in {'TOTP','EMAIL','APP'} or status not in {'ENABLED','DISABLED','PENDING'} or not isinstance(payload,dict): raise ValueError('P1_MFA_PAYLOAD_INVALID')
 e=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')); h=hashlib.sha256(e.encode()).hexdigest(); n=_now(); c.execute('INSERT INTO roadmap_p1_mfa_states(mfa_key,career_id,subject_id,method,status,payload_json,payload_hash,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(mfa_key) DO UPDATE SET career_id=excluded.career_id,subject_id=excluded.subject_id,method=excluded.method,status=excluded.status,payload_json=excluded.payload_json,payload_hash=excluded.payload_hash,updated_at=excluded.updated_at',(key.strip(),career_id,subject_id,method,status,e,h,n,n)); c.commit(); r=c.execute('SELECT * FROM roadmap_p1_mfa_states WHERE mfa_key=?',(key.strip(),)).fetchone(); return {**dict(r),'payload_json':json.loads(r['payload_json'])}
def read_p1_mfa_state(c,key=None):
 rows=c.execute('SELECT * FROM roadmap_p1_mfa_states'+(' WHERE mfa_key=?' if key else '')+' ORDER BY updated_at DESC',((key,) if key else ())).fetchall(); return [{**dict(r),'payload_json':json.loads(r['payload_json'])} for r in rows]
def audit_p1_mfas(c):
 rows=read_p1_mfas(c); bad=[x['item_id'] for x in rows if validate_p1_mfa(c,x['item_id'])['status']!='VALID']; checks={'count_10':len(rows)==10,'expected_ids':{x['item_id'] for x in rows}==set(ITEM_IDS),'all_consolidated':all(x['status']=='CONSOLIDATED' for x in rows),'sql_game_state':all(x['source_of_truth']=='SQL_GAMESTATE' for x in rows),'valid_contracts':not bad}; return {'status':'VALID' if all(checks.values()) else 'INVALID','mfa_count':len(rows),'state_count':c.execute('SELECT COUNT(*) FROM roadmap_p1_mfa_states').fetchone()[0],'checks':checks,'invalid_items':bad,'read_only':True}
def protect_p1_mfa_mutation(c,i,actor,payload):
 v=validate_p1_mfa(c,i); ok=actor=='AUTHORIZED_SQL_SERVICE' and v['status']=='VALID'; e=json.dumps(payload,sort_keys=True,separators=(',',':')); c.execute('INSERT OR REPLACE INTO roadmap_p1_mfa_audit(item_id,action,allowed,reason,payload,created_at) VALUES(?,?,?,?,?,?)',(i,'PROTECT_MUTATION',int(ok),'ALLOWED' if ok else 'SQL_SERVICE_AUTHORIZATION_REQUIRED',e,_now())); c.commit()
 if not ok: raise DomainError(DomainErrorCode.P0_MUTATION_AUTHORIZATION_REQUIRED)
 return {'allowed':True,'item_id':i,'payload_hash':hashlib.sha256(e.encode()).hexdigest()}
