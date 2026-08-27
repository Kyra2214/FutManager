from __future__ import annotations
from dataclasses import dataclass
from engine.sports.cycle import SCHEMA as SPORT_SCHEMA
from enum import StrEnum
from datetime import date
import json, random, sqlite3

from engine.core.state_store import assert_mutable_state_path
from engine.economy.institutional_power import InstitutionalPowerService
SCHEMA='''
CREATE TABLE IF NOT EXISTS club_ai_profiles(club_id INTEGER PRIMARY KEY,strategy TEXT NOT NULL DEFAULT 'BALANCED',aggressiveness INTEGER NOT NULL DEFAULT 50,risk_tolerance INTEGER NOT NULL DEFAULT 50,youth_focus INTEGER NOT NULL DEFAULT 50,market_focus INTEGER NOT NULL DEFAULT 50,result_focus INTEGER NOT NULL DEFAULT 50,young_preference INTEGER NOT NULL DEFAULT 50,experienced_preference INTEGER NOT NULL DEFAULT 50,salary_limit INTEGER NOT NULL DEFAULT 0,social_priority INTEGER NOT NULL DEFAULT 50,scouting_intensity INTEGER NOT NULL DEFAULT 50,autonomy INTEGER NOT NULL DEFAULT 50,seed INTEGER,version TEXT NOT NULL DEFAULT '1.0');
CREATE TABLE IF NOT EXISTS club_objectives(objective_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,type TEXT NOT NULL,priority INTEGER NOT NULL,deadline TEXT,status TEXT NOT NULL DEFAULT 'ACTIVE',origin TEXT,progress REAL NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS club_decision_history(decision_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,decision_date TEXT NOT NULL,type TEXT NOT NULL,decision TEXT NOT NULL,target TEXT,reason TEXT,priority INTEGER,alternatives TEXT,chosen TEXT,cost INTEGER,result TEXT,seed INTEGER,ai_version TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS club_ai_risk_limits(club_id INTEGER NOT NULL,season INTEGER NOT NULL,max_cost INTEGER NOT NULL,max_aggressiveness INTEGER NOT NULL DEFAULT 50,updated_at TEXT NOT NULL,PRIMARY KEY(club_id,season));
CREATE TABLE IF NOT EXISTS club_ai_approvals(decision_id INTEGER PRIMARY KEY,approved_by TEXT NOT NULL,approved_at TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'APPROVED');
'''
class Personality(StrEnum): CONSERVATIVE='CONSERVATIVE'; BALANCED='BALANCED'; AGGRESSIVE='AGGRESSIVE'; YOUTH_FOCUSED='YOUTH_FOCUSED'; STAR_FOCUSED='STAR_FOCUSED'; FINANCIAL='FINANCIAL'
@dataclass(frozen=True)
class ClubDiagnosis: club_id:int; needs:tuple[str,...]; unavailable:int; squad_size:int; cash:int; health:str
class ClubAI:
 def __init__(self,db):
  assert_mutable_state_path(db) if not isinstance(db,sqlite3.Connection) else None;self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db; self.connection.row_factory=sqlite3.Row; self.connection.execute('PRAGMA foreign_keys=ON'); self.connection.executescript(SCHEMA); self.connection.executescript(SPORT_SCHEMA)
  columns={row[1] for row in self.connection.execute('PRAGMA table_info(player_sport_state)')}
  for name,definition in {'recovery_days':'INTEGER NOT NULL DEFAULT 0','form':'INTEGER NOT NULL DEFAULT 50','category':"TEXT NOT NULL DEFAULT 'RESERVE'"}.items():
   if name not in columns: self.connection.execute(f'ALTER TABLE player_sport_state ADD COLUMN {name} {definition}')
  self.connection.commit()
 def set_profile(self,club_id,strategy=Personality.BALANCED,seed=None,**kwargs):
  cols={'aggressiveness':50,'risk_tolerance':50,'youth_focus':50,'market_focus':50,'result_focus':50,'young_preference':50,'experienced_preference':50,'salary_limit':0,'social_priority':50,'scouting_intensity':50,'autonomy':50}; cols.update(kwargs); self.connection.execute('insert or replace into club_ai_profiles(club_id,strategy,aggressiveness,risk_tolerance,youth_focus,market_focus,result_focus,young_preference,experienced_preference,salary_limit,social_priority,scouting_intensity,autonomy,seed) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(club_id,strategy.value if hasattr(strategy,'value') else strategy,*[cols[k] for k in cols],seed)); self.connection.commit()
 def add_objective(self,club_id,type_,priority=50,deadline=None,origin='board'): 
  cur=self.connection.execute('insert into club_objectives(club_id,type,priority,deadline,origin) values(?,?,?,?,?)',(club_id,type_,priority,deadline,origin)); self.connection.commit(); return int(cur.lastrowid)
 def diagnose(self,club_id):
  rows=self.connection.execute('select * from player_sport_state where club_id=?',(club_id,)).fetchall(); unavailable=sum(not bool(r['available']) for r in rows); needs=[]
  if len(rows)<16: needs.append('BUILD_SQUAD')
  if not any(r['category']=='FIRST_TEAM' for r in rows): needs.append('FIRST_TEAM')
  cash=self.connection.execute('select cash from club_economic_state where club_id=?',(club_id,)).fetchone(); health=self.connection.execute('select financial_status from club_economic_state where club_id=?',(club_id,)).fetchone(); return ClubDiagnosis(club_id,tuple(needs),unavailable,len(rows),cash[0] if cash else 0,health[0] if health else 'UNKNOWN')
 def evaluate_player(self,player_id,club_id):
  r=self.connection.execute('select j.*,s.form,s.condition,s.available,s.fatigue from jogadores j left join player_sport_state s on s.player_id=j.jogador_id where j.jogador_id=?',(player_id,)).fetchone()
  if not r: raise KeyError(player_id)
  p=self.connection.execute('select * from club_ai_profiles where club_id=?',(club_id,)).fetchone(); youth=p['young_preference'] if p else 50
  age_score=max(0,100-abs((r['idade'] or 25)-24)*4); form=r['form'] or 50; avail=100 if r['available'] else 0; score=age_score*.25+form*.25+avail*.15+(r['cr1'] or 0)*.2+(r['cr2'] or 0)*.15+youth*.05
  return {'player_id':player_id,'score':round(score,2),'available':bool(avail),'reason':'idade, forma, disponibilidade e atributos nativos disponíveis'}
 def propose_training(self,club_id):
  d=self.diagnose(club_id); p=self.connection.execute('select strategy from club_ai_profiles where club_id=?',(club_id,)).fetchone(); training='PHYSICAL' if d.unavailable else 'GENERAL'; return self._decision(club_id,'TRAINING',training,'reduzir indisponibilidade' if d.unavailable else 'manutenção do elenco',0)
 def _decision(self,club_id,type_,decision,reason,cost,target=None,seed=None,alternatives=None):
  alternatives=alternatives or []
  self.connection.execute('insert into club_decision_history(club_id,decision_date,type,decision,target,reason,priority,alternatives,chosen,cost,result,seed,ai_version) values(?,?,?,?,?,?,?,?,?,?,?,?,?)',(club_id,date.today().isoformat(),type_,decision,target,reason,50,json.dumps(alternatives,sort_keys=True),decision,cost,'PROPOSED',seed,'1.0')); self.connection.commit(); return decision
 def institutional_context(self,club_id):
  service=InstitutionalPowerService(self.connection); profile=service.get(club_id) or service.refresh(club_id); reputation=profile.overall_score
  if self.connection.execute("select 1 from sqlite_master where type='table' and name='club_reputation'").fetchone():
   columns={row[1] for row in self.connection.execute('pragma table_info(club_reputation)')}; fields=[name for name in ('sporting','national','international','commercial','historical') if name in columns]
   if fields:
    row=self.connection.execute('select '+','.join(fields)+' from club_reputation where club_id=?',(club_id,)).fetchone(); values=[float(row[name]) for name in fields if row[name] is not None] if row else []
    if values: reputation=sum(values)/len(values)
  return {'overall':profile.overall_score,'stars':profile.sponsor_stars,'squad':profile.squad_score,'ct':profile.ct_score,'stadium':profile.stadium_score,'reputation':round(reputation,2)}
 def prioritize_competitions(self,club_id,seed=None):
  context=self.institutional_context(club_id); rows=self.connection.execute("select competition_id,name,status from competitions where status in ('ACTIVE','PLANNED') order by competition_id").fetchall() if self.connection.execute("select 1 from sqlite_master where type='table' and name='competitions'").fetchone() else []
  ids=[int(row['competition_id']) for row in rows]; objective=self.connection.execute("select type from club_objectives where club_id=? and status='ACTIVE' order by priority desc,objective_id limit 1",(club_id,)).fetchone(); choice=ids[:1] if ids else []
  if objective and objective['type'].startswith('COMPETITION:'):
   try:
    target=int(objective['type'].split(':',1)[1]); choice=[target] if target in ids else choice
   except ValueError: pass
  return self._decision(club_id,'COMPETITION_PRIORITY',json.dumps(choice),'prioridade derivada do calendário e overall institucional',0,target=json.dumps(ids),seed=seed,alternatives=[str(i) for i in ids])
 def propose_market(self,club_id,seed=None):
  diagnosis=self.diagnose(club_id); profile=self.connection.execute('select * from club_ai_profiles where club_id=?',(club_id,)).fetchone(); cash=diagnosis.cash; limit=int(profile['salary_limit']) if profile else 0; context=self.institutional_context(club_id)
  if 'BUILD_SQUAD' in diagnosis.needs: decision='RECRUIT_SQUAD'; reason='elenco abaixo do mínimo operacional'; cost=0
  elif diagnosis.health in ('CRITICAL','INSOLVENT') or (limit and cash < limit): decision='HOLD_MARKET'; reason='caixa ou saúde financeira abaixo do limite'; cost=0
  elif context['overall'] < 40: decision='SCOUT_MARKET'; reason='overall institucional baixo; priorizar observação de baixo custo'; cost=0
  else: decision='SCOUT_MARKET'; reason='diagnóstico sem necessidade crítica'; cost=0
  return self._decision(club_id,'MARKET',decision,reason,cost,seed=seed,alternatives=['HOLD_MARKET','SCOUT_MARKET','RECRUIT_SQUAD'])
 def update_objective(self,objective_id,progress):
  value=max(0.0,min(100.0,float(progress))); row=self.connection.execute('select * from club_objectives where objective_id=?',(objective_id,)).fetchone()
  if not row: raise KeyError(objective_id)
  status='COMPLETED' if value>=100 else 'ACTIVE'; self.connection.execute('update club_objectives set progress=?,status=? where objective_id=?',(value,status,objective_id)); self.connection.commit(); return {'objective_id':objective_id,'progress':value,'status':status}
 def auto_lineup(self,club_id,seed=None):
  rows=self.connection.execute("select s.player_id,coalesce(pp.position_code,3) position_code from player_sport_state s left join player_positions pp on pp.player_id=s.player_id where s.club_id=? and s.available=1 and s.recovery_days=0 order by s.category='FIRST_TEAM' desc,s.form desc,s.player_id",(club_id,)).fetchall()
  selected=[int(r['player_id']) for r in rows[:11]]
  if len(selected)<11: return {'club_id':club_id,'valid':False,'player_ids':selected,'reason':'elenco disponível abaixo de 11 atletas'}
  formation='4-3-3' if len(selected)>=11 else '4-4-2'
  with self.connection:
   cur=self.connection.execute("insert into lineups(club_id,formation,created_at) values(?,?,?)",(club_id,formation,date.today().isoformat()))
   lineup_id=int(cur.lastrowid)
   for row in rows[:11]: self.connection.execute("insert into lineup_players(lineup_id,player_id,position_code) values(?,?,?)",(lineup_id,int(row['player_id']),int(row['position_code'])))
  self._decision(club_id,'LINEUP',formation,'escalação automática por disponibilidade, categoria e forma',0,target=str(lineup_id),seed=seed,alternatives=['4-3-3','4-4-2','5-3-2'])
  return {'club_id':club_id,'valid':True,'lineup_id':lineup_id,'formation':formation,'player_ids':selected}
 def choose_tactic(self,club_id,seed=None):
  profile=self.connection.execute('select * from club_ai_profiles where club_id=?',(club_id,)).fetchone(); strategy=profile['strategy'] if profile else 'BALANCED'; context=self.institutional_context(club_id)
  tactic={'CONSERVATIVE':'LOW_BLOCK','AGGRESSIVE':'HIGH_PRESS','YOUTH_FOCUSED':'POSSESSION','STAR_FOCUSED':'ATTACKING','FINANCIAL':'LOW_RISK'}.get(strategy,'BALANCED')
  if context['overall'] < 30 and tactic in ('HIGH_PRESS','ATTACKING'): tactic='BALANCED'
  return self._decision(club_id,'TACTIC',tactic,'personalidade e risco do perfil persistido',0,seed=seed,alternatives=['LOW_BLOCK','BALANCED','POSSESSION','HIGH_PRESS','ATTACKING'])
 def transfer_window_plan(self,club_id,season,week,seed=None):
  diagnosis=self.diagnose(club_id); priorities=['RETAIN_CORE']
  if 'BUILD_SQUAD' in diagnosis.needs: priorities.insert(0,'RECRUIT_STARTERS')
  if diagnosis.unavailable: priorities.append('COVER_UNAVAILABLE')
  return self._decision(club_id,'TRANSFER_WINDOW',json.dumps(priorities,sort_keys=True),'necessidades do elenco e caixa persistidos',0,target=f'{season}:{week}',seed=seed,alternatives=['RETAIN_CORE','RECRUIT_STARTERS','COVER_UNAVAILABLE','SELL_SURPLUS'])
 def propose_sale(self,club_id,player_id,seed=None):
  self.evaluate_player(player_id,club_id); return self._decision(club_id,'SALE', 'HOLD_SALE','venda somente após avaliação e limite financeiro',0,target=str(player_id),seed=seed,alternatives=['HOLD_SALE','LIST_FOR_SALE'])
 def propose_renewal(self,club_id,player_id,seed=None):
  self.evaluate_player(player_id,club_id); return self._decision(club_id,'RENEWAL','RENEW_CORE','manter atleta avaliado como núcleo do elenco',0,target=str(player_id),seed=seed,alternatives=['RENEW_CORE','DEFER_RENEWAL'])
 def propose_department_upgrade(self,club_id,department,seed=None):
  diagnosis=self.diagnose(club_id); decision='HOLD_UPGRADE' if diagnosis.health in ('CRITICAL','INSOLVENT') else 'UPGRADE_DEPARTMENT'
  return self._decision(club_id,'DEPARTMENT',decision,'saúde financeira e necessidade institucional persistidas',0,target=department,seed=seed,alternatives=['HOLD_UPGRADE','UPGRADE_DEPARTMENT'])
 def evolve_department(self,club_id,department,seed=None):
  context=self.institutional_context(club_id); decision='HOLD_UPGRADE' if context['overall'] < 35 else 'UPGRADE_DEPARTMENT'
  reason='overall baixo; preservar caixa' if decision == 'HOLD_UPGRADE' else 'melhorar capacidade institucional conforme overall persistido'
  return self._decision(club_id,'DEPARTMENT_AI',decision,reason,0,target=department,seed=seed,alternatives=['HOLD_UPGRADE','UPGRADE_DEPARTMENT'])
 def weekly_cycle(self,club_id,seed=None):
  existing=self.connection.execute("select * from club_decision_history where club_id=? and type='WEEKLY_CYCLE' and seed=? order by decision_id desc limit 1",(club_id,seed)).fetchone()
  if existing: return {'club_id':club_id,'seed':seed,'idempotent':True,'decisions':json.loads(existing['decision'])}
  training=self.propose_training(club_id); market=self.propose_market(club_id,seed); tactic=self.choose_tactic(club_id,seed); priority=self.prioritize_competitions(club_id,seed); window=self.transfer_window_plan(club_id,2026,1,seed); lineup=self.auto_lineup(club_id,seed); decisions={'training':training,'market':market,'tactic':tactic,'priority':priority,'window':window,'lineup':lineup}
  self._decision(club_id,'WEEKLY_CYCLE',json.dumps(decisions,sort_keys=True),'decisões semanais derivadas do diagnóstico',0,seed=seed)
  return {'club_id':club_id,'seed':seed,'idempotent':False,'decisions':decisions}
 def strategic_preview(self, club_id: int, season: int, strategy: str, estimated_cost: int) -> dict:
  diagnosis=self.diagnose(club_id); limit=self.connection.execute('SELECT max_cost FROM club_ai_risk_limits WHERE club_id=? AND season=?',(club_id,season)).fetchone(); max_cost=int(limit['max_cost']) if limit else None
  incompatible=bool(max_cost is not None and int(estimated_cost)>max_cost) or diagnosis.health in ('CRITICAL','INSOLVENT')
  return {'club_id':int(club_id),'season':int(season),'strategy':str(strategy),'estimated_cost':int(estimated_cost),'risk_limit':max_cost,'incompatible':incompatible,'reason':'limite de risco ou saúde financeira persistidos' if incompatible else 'compatível com o diagnóstico persistido','persisted':False}

 def approve_strategy(self, club_id: int, season: int, strategy: str, estimated_cost: int, approved_by: str = 'board') -> dict:
  preview=self.strategic_preview(club_id,season,strategy,estimated_cost)
  if preview['incompatible']: raise ValueError('STRATEGY_RISK_LIMIT')
  decision=self._decision(club_id,'STRATEGY',strategy,'aprovação baseada no diagnóstico econômico persistido',int(estimated_cost),target=str(season),alternatives=['HOLD','REVIEW'])
  row=self.connection.execute("SELECT decision_id FROM club_decision_history WHERE club_id=? AND type='STRATEGY' ORDER BY decision_id DESC LIMIT 1",(club_id,)).fetchone()
  self.approve_decision(row['decision_id'],approved_by)
  return {'decision_id':int(row['decision_id']),'status':'APPROVED','preview':preview}

 def explain_diagnosis(self, club_id: int) -> dict:
  payload=self.diagnostic_payload(club_id)
  facts=[{'field':'squad_size','value':payload['squad_size'],'source':'player_sport_state'},{'field':'unavailable','value':payload['unavailable'],'source':'player_sport_state'},{'field':'cash','value':payload['cash'],'source':'club_economic_state'},{'field':'health','value':payload['health'],'source':'club_economic_state'}]
  return {'club_id':int(club_id),'needs':payload['needs'],'facts':facts,'persisted':True}

 def approve_decision(self, decision_id: int, approved_by: str = 'manager'):
  row=self.connection.execute('select decision_id from club_decision_history where decision_id=?',(int(decision_id),)).fetchone()
  if not row: raise KeyError(decision_id)
  self.connection.execute('INSERT OR REPLACE INTO club_ai_approvals(decision_id,approved_by,approved_at,status) VALUES(?,?,?,?)',(int(decision_id),str(approved_by),date.today().isoformat(),'APPROVED')); self.connection.commit()
  return {'decision_id':int(decision_id),'approved_by':str(approved_by),'status':'APPROVED','persisted':True}

 def decision_audit(self, club_id: int, seed: int | None = None):
  query='SELECT h.*,a.approved_by,a.status AS approval_status FROM club_decision_history h LEFT JOIN club_ai_approvals a ON a.decision_id=h.decision_id WHERE h.club_id=?'
  args=[int(club_id)]
  if seed is not None: query+=' AND h.seed=?'; args.append(seed)
  rows=[dict(row) for row in self.connection.execute(query+' ORDER BY h.decision_id',args).fetchall()]
  return {'club_id':int(club_id),'seed':seed,'decisions':rows,'count':len(rows),'persisted':True}

 def diagnostic_payload(self,club_id):
  diagnosis=self.diagnose(club_id); return {'club_id':club_id,'needs':list(diagnosis.needs),'unavailable':diagnosis.unavailable,'squad_size':diagnosis.squad_size,'cash':diagnosis.cash,'health':diagnosis.health,'institutional':self.institutional_context(club_id),'objectives':[dict(row) for row in self.connection.execute('select * from club_objectives where club_id=? order by priority desc,objective_id',(club_id,)).fetchall()]}
 def set_risk_limit(self,club_id,season,max_cost,max_aggressiveness=50):
  if min(int(max_cost), int(max_aggressiveness)) < 0: raise ValueError('AI_RISK_LIMIT_INVALID')
  self.connection.execute('INSERT INTO club_ai_risk_limits(club_id,season,max_cost,max_aggressiveness,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(club_id,season) DO UPDATE SET max_cost=excluded.max_cost,max_aggressiveness=excluded.max_aggressiveness,updated_at=excluded.updated_at',(club_id,season,int(max_cost),int(max_aggressiveness),date.today().isoformat())); self.connection.commit(); return dict(self.connection.execute('SELECT * FROM club_ai_risk_limits WHERE club_id=? AND season=?',(club_id,season)).fetchone())
 def preview_decision(self,club_id,type_,decision,target=None,cost=0,season=2026):
  limit=self.connection.execute('SELECT * FROM club_ai_risk_limits WHERE club_id=? AND season=?',(club_id,season)).fetchone(); allowed=not limit or int(cost)<=int(limit['max_cost'])
  return {'club_id':club_id,'type':type_,'decision':decision,'target':target,'cost':int(cost),'allowed':allowed,'requires_approval':True,'persisted':False,'reason':'prévia derivada de fatos e limites persistidos','risk_limit':dict(limit) if limit else None}
 def approve_decision(self,decision_id,approved_by='manager'):
  row=self.connection.execute('SELECT * FROM club_decision_history WHERE decision_id=?',(decision_id,)).fetchone()
  if not row: raise KeyError(decision_id)
  if row['result']=='APPROVED': return {'decision_id':decision_id,'status':'APPROVED','idempotent':True}
  if row['result'] not in ('PROPOSED','PENDING'): raise ValueError('AI_DECISION_NOT_APPROVABLE')
  self.connection.execute('INSERT OR REPLACE INTO club_ai_approvals(decision_id,approved_by,approved_at,status) VALUES(?,?,?,?)',(decision_id,approved_by,date.today().isoformat(),'APPROVED')); self.connection.execute("UPDATE club_decision_history SET result='APPROVED' WHERE decision_id=?",(decision_id,)); self.connection.commit(); return {'decision_id':decision_id,'status':'APPROVED','idempotent':False}
 def budget_alerts(self,club_id,season=2026):
  limit=self.connection.execute('SELECT max_cost FROM club_ai_risk_limits WHERE club_id=? AND season=?',(club_id,season)).fetchone(); max_cost=int(limit['max_cost']) if limit else None
  query="SELECT decision_id,type,decision,cost,result,target FROM club_decision_history WHERE club_id=? AND result IN ('PROPOSED','PENDING') AND cost>0"; args=[club_id]
  if max_cost is not None: query += ' AND cost>?'; args.append(max_cost)
  return self.connection.execute(query+' ORDER BY decision_id DESC',args).fetchall()
 def history(self,club_id): return self.connection.execute('select * from club_decision_history where club_id=? order by decision_id desc',(club_id,)).fetchall()
 def close(self): self.connection.close()
