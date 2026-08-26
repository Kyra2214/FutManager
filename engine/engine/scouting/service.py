from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
import json, random, sqlite3

from engine.core.state_store import assert_mutable_state_path
SCHEMA='''
CREATE TABLE IF NOT EXISTS scout_missions(mission_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,scout_id INTEGER NOT NULL,start_date TEXT NOT NULL,end_date TEXT NOT NULL,region TEXT,position_code INTEGER,min_age INTEGER,max_age INTEGER,min_strength INTEGER,min_potential INTEGER,status TEXT NOT NULL DEFAULT 'PLANNED',seed INTEGER,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS scout_opportunities(opportunity_id INTEGER PRIMARY KEY AUTOINCREMENT,mission_id INTEGER NOT NULL,player_id INTEGER NOT NULL,club_id INTEGER,position_code INTEGER,age INTEGER,strength INTEGER,potential INTEGER,estimated_value INTEGER,contract TEXT,observations TEXT,confidence REAL,priority INTEGER,knowledge TEXT NOT NULL DEFAULT 'OBSERVED',available INTEGER NOT NULL DEFAULT 1,UNIQUE(mission_id,player_id),FOREIGN KEY(mission_id) REFERENCES scout_missions(mission_id));
CREATE TABLE IF NOT EXISTS scout_reports(report_id INTEGER PRIMARY KEY AUTOINCREMENT,mission_id INTEGER NOT NULL UNIQUE,created_at TEXT NOT NULL,seed INTEGER,summary TEXT,FOREIGN KEY(mission_id) REFERENCES scout_missions(mission_id));
CREATE TABLE IF NOT EXISTS scout_regions(region TEXT PRIMARY KEY,enabled INTEGER NOT NULL DEFAULT 1,cost_multiplier REAL NOT NULL DEFAULT 1.0);
CREATE TABLE IF NOT EXISTS academy_players(player_id INTEGER PRIMARY KEY,club_id INTEGER NOT NULL,progress REAL NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'YOUTH',maintenance_cost INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS opponent_observations(observation_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,opponent_id INTEGER NOT NULL,competition_id INTEGER,season INTEGER NOT NULL,style TEXT NOT NULL,weakness TEXT NOT NULL,evidence TEXT NOT NULL,confidence REAL NOT NULL,sample_size INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'ACTIVE',expires_at TEXT NOT NULL,UNIQUE(club_id,opponent_id,competition_id,season));
CREATE TABLE IF NOT EXISTS game_plans(plan_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,opponent_id INTEGER NOT NULL,observation_id INTEGER NOT NULL,plan TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'PREVIEW',approved_by TEXT,approved_at TEXT);
'''
class MissionStatus(StrEnum): PLANNED='PLANNED'; ACTIVE='ACTIVE'; COMPLETED='COMPLETED'; CANCELLED='CANCELLED'
class Knowledge(StrEnum): UNKNOWN='UNKNOWN'; OBSERVED='OBSERVED'; SCOUTED='SCOUTED'; CONFIRMED='CONFIRMED'
@dataclass(frozen=True)
class ScoutMission:
 mission_id:int; club_id:int; scout_id:int; start_date:str; end_date:str; status:str
class ScoutService:
 def __init__(self,db):
  assert_mutable_state_path(db) if not isinstance(db,sqlite3.Connection) else None;self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db; self.connection.row_factory=sqlite3.Row; self.connection.execute('PRAGMA foreign_keys=ON'); self.connection.executescript(SCHEMA)
  columns={row[1] for row in self.connection.execute('pragma table_info(scout_missions)')}
  for name,definition in {'cost':'INTEGER NOT NULL DEFAULT 0','priority':'INTEGER NOT NULL DEFAULT 50'}.items():
   if name not in columns: self.connection.execute(f'alter table scout_missions add column {name} {definition}')
  self.connection.commit()
 def regions(self): return self.connection.execute('select * from scout_regions where enabled=1 order by region').fetchall()
 def create_region(self,region:str,cost_multiplier:float=1.0):
  if not region.strip() or cost_multiplier<=0: raise ValueError('REGION_INVALID')
  self.connection.execute('insert or replace into scout_regions(region,cost_multiplier) values(?,?)',(region.strip(),cost_multiplier)); self.connection.commit()
 def create_mission(self,club_id:int,scout_id:int,start_date:str,duration_months:int,region=None,position_code=None,min_age=None,max_age=None,min_strength=None,min_potential=None,seed=None,priority:int=50)->int:
  if duration_months not in (1,2,3,6): raise ValueError('INVALID_DURATION')
  if not self.connection.execute('select 1 from staff_members where staff_id=? and role=?',(scout_id,'scout')).fetchone(): raise ValueError('SCOUT_NOT_FOUND')
  y,m,d=map(int,start_date.split('-')); end_month=m+duration_months; y+=(end_month-1)//12; end_month=(end_month-1)%12+1; end=f'{y:04d}-{end_month:02d}-{min(d,28):02d}'
  multiplier=1.0
  if region:
   found=self.connection.execute('select cost_multiplier from scout_regions where region=? and enabled=1',(region,)).fetchone()
   if found: multiplier=float(found['cost_multiplier'])
  cost=int(duration_months*1000*multiplier)
  cur=self.connection.execute('insert into scout_missions(club_id,scout_id,start_date,end_date,region,position_code,min_age,max_age,min_strength,min_potential,seed,created_at,cost,priority) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(club_id,scout_id,start_date,end,region,position_code,min_age,max_age,min_strength,min_potential,seed,date.today().isoformat(),cost,priority)); self.connection.commit(); return int(cur.lastrowid)
 def start(self,mission_id:int): self._set(mission_id,'ACTIVE')
 def cancel(self,mission_id:int): self._set(mission_id,'CANCELLED')
 def complete(self,mission_id:int,as_of:str|None=None,limit:int=20):
  m=self._mission(mission_id); as_of=as_of or date.today().isoformat()
  if m['status']=='CANCELLED': raise ValueError('MISSION_CANCELLED')
  if as_of < m['end_date']: raise ValueError('MISSION_NOT_DUE')
  rng=random.Random(m['seed']); query='select j.jogador_id,j.nome,j.idade,j.posicao_codigo,j.cr1,j.cr2,jt.time_id from jogadores j join jogador_time jt on jt.jogador_id=j.jogador_id where 1=1'; args=[]
  if m['position_code'] is not None: query+=' and j.posicao_codigo=?'; args.append(m['position_code'])
  if m['min_age'] is not None: query+=' and j.idade>=?'; args.append(m['min_age'])
  if m['max_age'] is not None: query+=' and j.idade<=?'; args.append(m['max_age'])
  if m['min_strength'] is not None: query+=' and ((j.cr1+j.cr2)/2)>=?'; args.append(m['min_strength'])
  if m['min_potential'] is not None: query+=' and ((j.cr1+j.cr2)/2)>=?'; args.append(m['min_potential'])
  rows=self.connection.execute(query,args).fetchall(); rng.shuffle(rows); rows=rows[:limit]
  for r in rows:
   strength=None; potential=None; value=None; confidence=.45
   self.connection.execute('insert or ignore into scout_opportunities(mission_id,player_id,club_id,position_code,age,strength,potential,estimated_value,observations,confidence,priority,knowledge) values(?,?,?,?,?,?,?,?,?,?,?,?)',(mission_id,r['jogador_id'],r['time_id'],r['posicao_codigo'],r['idade'],strength,potential,value,'atributos avançados não disponíveis na fonte',confidence,1,Knowledge.OBSERVED.value))
  self.connection.execute('update scout_missions set status=? where mission_id=?',(MissionStatus.COMPLETED.value,mission_id)); self.connection.execute('insert or replace into scout_reports(mission_id,created_at,seed,summary) values(?,?,?,?)',(mission_id,date.today().isoformat(),m['seed'],json.dumps({'count':len(rows),'discovery':'partial'},ensure_ascii=False))); self.connection.commit(); return self.connection.execute('select * from scout_opportunities where mission_id=?',(mission_id,)).fetchall()
 def opportunities(self,mission_id:int,position_code=None,min_age=None,max_age=None,min_potential=None):
  query='select * from scout_opportunities where mission_id=?'; args=[mission_id]
  if position_code is not None: query+=' and position_code=?'; args.append(position_code)
  if min_age is not None: query+=' and age>=?'; args.append(min_age)
  if max_age is not None: query+=' and age<=?'; args.append(max_age)
  if min_potential is not None: query+=' and potential>=?'; args.append(min_potential)
  return self.connection.execute(query+' order by priority desc,opportunity_id',args).fetchall()
 def academy_enroll(self,player_id:int,club_id:int,maintenance_cost:int=0):
  player=self.connection.execute('select jogador_id from jogadores where jogador_id=?',(player_id,)).fetchone()
  if not player or maintenance_cost<0: raise ValueError('ACADEMY_PLAYER_INVALID')
  self.connection.execute('insert or replace into academy_players(player_id,club_id,progress,status,maintenance_cost) values(?,?,coalesce((select progress from academy_players where player_id=?),0),coalesce((select status from academy_players where player_id=?),\'YOUTH\'),?)',(player_id,club_id,player_id,player_id,maintenance_cost)); self.connection.commit(); return dict(self.connection.execute('select * from academy_players where player_id=?',(player_id,)).fetchone())
 def academy_progress(self,player_id:int,amount:float):
  row=self.connection.execute('select * from academy_players where player_id=?',(player_id,)).fetchone()
  if not row or amount<0: raise ValueError('ACADEMY_PLAYER_INVALID')
  progress=min(100.0,float(row['progress'])+amount); status='READY' if progress>=100 else row['status']; self.connection.execute('update academy_players set progress=?,status=? where player_id=?',(progress,status,player_id)); self.connection.commit(); return dict(self.connection.execute('select * from academy_players where player_id=?',(player_id,)).fetchone())
 def academy_promote(self,player_id:int,approved:bool):
  row=self.connection.execute('select * from academy_players where player_id=?',(player_id,)).fetchone()
  if not row: raise KeyError(player_id)
  if not approved: return {'promoted':False,'player_id':player_id}
  if row['status']!='READY': raise ValueError('ACADEMY_NOT_READY')
  self.connection.execute('update academy_players set status=\'PROMOTED\' where player_id=?',(player_id,)); self.connection.execute('insert or ignore into jogador_time(jogador_id,time_id,status) values(?,?,?)',(player_id,row['club_id'],'Reserva')); self.connection.commit(); return {'promoted':True,'player_id':player_id,'club_id':row['club_id']}
 def academy_maintenance(self,club_id:int): return self.connection.execute('select * from academy_players where club_id=? order by player_id',(club_id,)).fetchall()
 def observe_opponent(self,club_id,opponent_id,competition_id,season,style,weakness,evidence,confidence,sample_size,expires_at):
  if not str(evidence).strip() or not 0 <= float(confidence) <= 1 or int(sample_size) < 1: raise ValueError('OBSERVATION_INVALID')
  with self.connection:
   self.connection.execute('INSERT INTO opponent_observations(club_id,opponent_id,competition_id,season,style,weakness,evidence,confidence,sample_size,expires_at) VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(club_id,opponent_id,competition_id,season) DO UPDATE SET style=excluded.style,weakness=excluded.weakness,evidence=excluded.evidence,confidence=excluded.confidence,sample_size=excluded.sample_size,expires_at=excluded.expires_at,status=\'ACTIVE\'',(club_id,opponent_id,competition_id,season,style,weakness,evidence,confidence,sample_size,expires_at))
  return dict(self.connection.execute('SELECT * FROM opponent_observations WHERE club_id=? AND opponent_id=? AND competition_id=? AND season=?',(club_id,opponent_id,competition_id,season)).fetchone())
 def opponent_report(self,club_id,opponent_id,competition_id=None,season=None):
  query='SELECT * FROM opponent_observations WHERE club_id=? AND opponent_id=?'; args=[club_id,opponent_id]
  if competition_id is not None: query+=' AND competition_id=?'; args.append(competition_id)
  if season is not None: query+=' AND season=?'; args.append(season)
  rows=[dict(r) for r in self.connection.execute(query+' ORDER BY observation_id DESC',args).fetchall()]
  return {'club_id':club_id,'opponent_id':opponent_id,'reports':rows,'quality':round(sum(r['confidence']*min(1,r['sample_size']/5) for r in rows)/len(rows),3) if rows else 0.0}
 def preview_game_plan(self,club_id,opponent_id,observation_id,plan):
  if not self.connection.execute('SELECT 1 FROM opponent_observations WHERE observation_id=? AND club_id=? AND opponent_id=?',(observation_id,club_id,opponent_id)).fetchone(): raise KeyError(observation_id)
  return {'club_id':club_id,'opponent_id':opponent_id,'observation_id':observation_id,'plan':plan,'persisted':False}
 def approve_game_plan(self,club_id,opponent_id,observation_id,plan,approved_by='manager'):
  preview=self.preview_game_plan(club_id,opponent_id,observation_id,plan)
  with self.connection: cur=self.connection.execute('INSERT INTO game_plans(club_id,opponent_id,observation_id,plan,status,approved_by,approved_at) VALUES(?,?,?,?,?,?,?)',(club_id,opponent_id,observation_id,plan,'APPROVED',approved_by,date.today().isoformat()))
  return {'plan_id':int(cur.lastrowid),'status':'APPROVED','preview':preview}
 def expire_opponent_reports(self,as_of):
  with self.connection: cur=self.connection.execute("UPDATE opponent_observations SET status='EXPIRED' WHERE status='ACTIVE' AND expires_at<?",(as_of,))
  return int(cur.rowcount)
 def compare_opponents(self,club_id,opponent_ids,competition_id,season):
  result=[]
  for opponent_id in opponent_ids:
   report=self.opponent_report(club_id,opponent_id,competition_id,season); result.append({'opponent_id':opponent_id,'quality':report['quality'],'styles':[r['style'] for r in report['reports']],'weaknesses':[r['weakness'] for r in report['reports']]})
  return result

 def compare(self,opportunity_id:int):
  row=self.connection.execute('select * from scout_opportunities where opportunity_id=?',(opportunity_id,)).fetchone()
  if not row: raise KeyError(opportunity_id)
  player=self.connection.execute('select jogador_id,nome,idade,cr1,cr2,posicao_codigo from jogadores where jogador_id=?',(row['player_id'],)).fetchone()
  return {'opportunity':dict(row),'actual':dict(player) if player else None,'comparison_available':player is not None}
 def confirm_recruitment(self,opportunity_id:int,approved:bool):
  row=self.connection.execute('select * from scout_opportunities where opportunity_id=?',(opportunity_id,)).fetchone()
  if not row: raise KeyError(opportunity_id)
  if not approved: return {'approved':False,'opportunity_id':opportunity_id}
  if not row['available']: raise ValueError('OPPORTUNITY_UNAVAILABLE')
  self.connection.execute('update scout_opportunities set available=0,knowledge=? where opportunity_id=?',(Knowledge.CONFIRMED.value,opportunity_id)); self.connection.commit(); return {'approved':True,'opportunity_id':opportunity_id,'player_id':row['player_id']}
 def _mission(self,i):
  r=self.connection.execute('select * from scout_missions where mission_id=?',(i,)).fetchone()
  if not r: raise KeyError(i)
  return r
 def _set(self,i,status): self._mission(i); self.connection.execute('update scout_missions set status=? where mission_id=?',(status,i)); self.connection.commit()
 def close(self): self.connection.close()
