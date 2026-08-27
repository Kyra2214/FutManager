from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
import json, random, sqlite3

from engine.core.state_store import assert_mutable_state_path
SCHEMA='''
CREATE TABLE IF NOT EXISTS player_sport_state(player_id INTEGER PRIMARY KEY,club_id INTEGER,category TEXT NOT NULL DEFAULT 'RESERVE',condition INTEGER NOT NULL DEFAULT 100,fatigue INTEGER NOT NULL DEFAULT 0,form INTEGER NOT NULL DEFAULT 50,training TEXT NOT NULL DEFAULT 'GENERAL',available INTEGER NOT NULL DEFAULT 1,current_injury_id INTEGER,recovery_days INTEGER NOT NULL DEFAULT 0,recent_minutes INTEGER NOT NULL DEFAULT 0,recent_matches INTEGER NOT NULL DEFAULT 0,last_updated TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS injuries(injury_id INTEGER PRIMARY KEY AUTOINCREMENT,player_id INTEGER NOT NULL,injury_type TEXT NOT NULL,start_date TEXT NOT NULL,estimated_days INTEGER NOT NULL,end_date TEXT NOT NULL,severity TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'ACTIVE');
CREATE TABLE IF NOT EXISTS player_suspensions(player_id INTEGER PRIMARY KEY,until_date TEXT NOT NULL,reason TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS club_player_roles(club_id INTEGER NOT NULL,role TEXT NOT NULL,player_id INTEGER NOT NULL,updated_at TEXT NOT NULL,PRIMARY KEY(club_id,role));
CREATE TABLE IF NOT EXISTS tactical_decision_history(decision_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,match_id INTEGER,event_type TEXT NOT NULL,decision_date TEXT NOT NULL,payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS lineup_confirmations(confirmation_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,competition_id INTEGER NOT NULL,lineup_id INTEGER NOT NULL,match_id INTEGER,confirmed_at TEXT NOT NULL,UNIQUE(club_id,competition_id,lineup_id,match_id));
CREATE TABLE IF NOT EXISTS sport_history(history_id INTEGER PRIMARY KEY AUTOINCREMENT,player_id INTEGER NOT NULL,event_type TEXT NOT NULL,event_date TEXT NOT NULL,payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS lineups(lineup_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,formation TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS lineup_players(lineup_id INTEGER NOT NULL,player_id INTEGER NOT NULL,position_code INTEGER NOT NULL,starter INTEGER NOT NULL DEFAULT 1,PRIMARY KEY(lineup_id,player_id),FOREIGN KEY(lineup_id) REFERENCES lineups(lineup_id));
CREATE TABLE IF NOT EXISTS saved_formations(saved_formation_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,competition_id INTEGER NOT NULL,name TEXT NOT NULL,formation TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,UNIQUE(club_id,competition_id,name));
CREATE TABLE IF NOT EXISTS saved_formation_players(saved_formation_id INTEGER NOT NULL,player_id INTEGER NOT NULL,position_code INTEGER NOT NULL,starter INTEGER NOT NULL DEFAULT 1,PRIMARY KEY(saved_formation_id,player_id),FOREIGN KEY(saved_formation_id) REFERENCES saved_formations(saved_formation_id));
CREATE TABLE IF NOT EXISTS player_positions(player_id INTEGER PRIMARY KEY,position_code INTEGER NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS substitution_plans(plan_id INTEGER PRIMARY KEY AUTOINCREMENT,lineup_id INTEGER NOT NULL,minute_target INTEGER NOT NULL,outgoing_player_id INTEGER NOT NULL,incoming_player_id INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'PLANNED',applied_minute INTEGER,created_at TEXT NOT NULL,UNIQUE(lineup_id,minute_target,outgoing_player_id),FOREIGN KEY(lineup_id) REFERENCES lineups(lineup_id));
CREATE TABLE IF NOT EXISTS player_match_stats(match_id INTEGER NOT NULL,player_id INTEGER NOT NULL,minutes INTEGER DEFAULT 0,goals INTEGER DEFAULT 0,assists INTEGER DEFAULT 0,cards INTEGER DEFAULT 0,rating REAL,PRIMARY KEY(match_id,player_id));
CREATE TABLE IF NOT EXISTS match_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT,match_id INTEGER NOT NULL,event_type TEXT NOT NULL,minute INTEGER,player_id INTEGER,payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tactical_profiles(profile_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,name TEXT NOT NULL,formation TEXT NOT NULL,instructions TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,UNIQUE(club_id,name));
CREATE TABLE IF NOT EXISTS lineup_history(history_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,lineup_id INTEGER NOT NULL,event_type TEXT NOT NULL,created_at TEXT NOT NULL,payload TEXT NOT NULL);
'''
class SquadCategory(StrEnum): FIRST_TEAM='FIRST_TEAM'; RESERVE='RESERVE'; YOUTH='YOUTH'
class TrainingType(StrEnum): GENERAL='GENERAL'; ATTACK='ATTACK'; DEFENCE='DEFENCE'; PHYSICAL='PHYSICAL'; TECHNICAL='TECHNICAL'; GOALKEEPER='GOALKEEPER'
class InjuryStatus(StrEnum): ACTIVE='ACTIVE'; RECOVERING='RECOVERING'; RECOVERED='RECOVERED'
@dataclass(frozen=True)
class Lineup: lineup_id:int; club_id:int; formation:str; player_ids:tuple[int,...]
class SportStateStore:
 def __init__(self,db):
  assert_mutable_state_path(db) if not isinstance(db,sqlite3.Connection) else None;self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db; self.connection.row_factory=sqlite3.Row; self.connection.execute('PRAGMA foreign_keys=ON'); self.connection.executescript(SCHEMA); self.connection.commit()
 def ensure_player(self,player_id,club_id,category=SquadCategory.RESERVE,position_code=3):
  now=date.today().isoformat()
  self.connection.execute('insert or ignore into player_sport_state(player_id,club_id,category,last_updated) values(?,?,?,?)',(player_id,club_id,category.value,now))
  self.connection.execute('insert into player_positions(player_id,position_code,updated_at) values(?,?,?) on conflict(player_id) do update set position_code=excluded.position_code,updated_at=excluded.updated_at',(player_id,int(position_code),now)); self.connection.commit()
 def squad(self,club_id,category=None):
  q='select * from player_sport_state where club_id=?'; a=[club_id]
  if category: q+=' and category=?'; a.append(category.value if hasattr(category,'value') else category)
  return self.connection.execute(q,a).fetchall()

 def squad_summary(self, club_id):
  rows = self.squad(club_id)
  starters = [row for row in rows if row['category'] == SquadCategory.FIRST_TEAM.value]
  reserves = [row for row in rows if row['category'] == SquadCategory.RESERVE.value]
  unavailable = [row for row in rows if not row['available'] or row['recovery_days'] > 0 or self.is_suspended(row['player_id'])]
  return {'club_id': club_id, 'total': len(rows), 'starters': len(starters), 'reserves': len(reserves), 'unavailable': len(unavailable), 'available': len(rows) - len(unavailable)}

 def squad_depth_report(self, club_id):
  rows=self.connection.execute('SELECT s.player_id,s.category,s.available,s.recovery_days,COALESCE(p.position_code,3) AS position_code FROM player_sport_state s LEFT JOIN player_positions p ON p.player_id=s.player_id WHERE s.club_id=? ORDER BY position_code,s.category,s.player_id',(int(club_id),)).fetchall()
  grouped={}
  for row in rows:
   position=int(row['position_code']); bucket=grouped.setdefault(position,{'position_code':position,'total':0,'first_team':0,'reserve':0,'youth':0,'available':0,'unavailable':0,'suspended':0,'player_ids':[]})
   bucket['total']+=1; bucket['player_ids'].append(int(row['player_id']))
   category=str(row['category']).lower()
   if category == SquadCategory.FIRST_TEAM.value.lower(): bucket['first_team']+=1
   elif category == SquadCategory.RESERVE.value.lower(): bucket['reserve']+=1
   elif category == SquadCategory.YOUTH.value.lower(): bucket['youth']+=1
   unavailable=not row['available'] or row['recovery_days']>0 or self.is_suspended(row['player_id'])
   bucket['unavailable']+=int(unavailable); bucket['available']+=int(not unavailable); bucket['suspended']+=int(self.is_suspended(row['player_id']))
  return {'club_id':int(club_id),'positions':tuple(grouped[position] for position in sorted(grouped))}

 def create_tactical_profile(self, club_id, name, formation, instructions=None):
  if not str(name).strip() or not formation or '-' not in formation: raise ValueError('INVALID_TACTICAL_PROFILE')
  encoded=json.dumps(instructions if isinstance(instructions,dict) else {},ensure_ascii=False,sort_keys=True,separators=(',',':'))
  now=date.today().isoformat()
  self.connection.execute('INSERT INTO tactical_profiles(club_id,name,formation,instructions,created_at,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(club_id,name) DO UPDATE SET formation=excluded.formation,instructions=excluded.instructions,updated_at=excluded.updated_at',(int(club_id),str(name).strip(),formation,encoded,now,now)); self.connection.commit()
  row=self.connection.execute('SELECT * FROM tactical_profiles WHERE club_id=? AND name=?',(int(club_id),str(name).strip())).fetchone(); result=dict(row); result['instructions']=json.loads(result['instructions']); return result

 def tactical_profiles(self, club_id):
  return [dict(row, instructions=json.loads(row['instructions'])) for row in self.connection.execute('SELECT * FROM tactical_profiles WHERE club_id=? ORDER BY name',(int(club_id),)).fetchall()]

 def preview_lineup(self, club_id, competition_id, name):
  saved=self.saved_formation(club_id, competition_id, name)
  available=tuple(int(row['player_id']) for row in self.connection.execute('SELECT player_id FROM player_sport_state WHERE club_id=? AND available=1 AND recovery_days=0 ORDER BY player_id',(int(club_id),)).fetchall())
  missing=tuple(pid for pid in saved['player_ids'] if pid not in available)
  return {'club_id':int(club_id),'competition_id':int(competition_id),'name':name,'formation':saved['formation'],'player_ids':saved['player_ids'],'unavailable_player_ids':missing,'valid':len(saved['player_ids'])>=11 and not missing,'persisted':False}

 def set_player_role(self, club_id, role, player_id):
  allowed={'CAPTAIN','PENALTY_TAKER','FREE_KICK_TAKER','CORNER_TAKER'}
  role=str(role).upper()
  if role not in allowed: raise ValueError('INVALID_PLAYER_ROLE')
  row=self.connection.execute('SELECT club_id FROM player_sport_state WHERE player_id=?',(int(player_id),)).fetchone()
  if not row or row['club_id'] != int(club_id) or not self.is_available(player_id): raise ValueError('player unavailable or outside club')
  self.connection.execute('INSERT INTO club_player_roles(club_id,role,player_id,updated_at) VALUES(?,?,?,?) ON CONFLICT(club_id,role) DO UPDATE SET player_id=excluded.player_id,updated_at=excluded.updated_at',(int(club_id),role,int(player_id),date.today().isoformat())); self.connection.commit()
  return dict(self.connection.execute('SELECT * FROM club_player_roles WHERE club_id=? AND role=?',(int(club_id),role)).fetchone())

 def player_roles(self, club_id):
  return [dict(row) for row in self.connection.execute('SELECT * FROM club_player_roles WHERE club_id=? ORDER BY role',(int(club_id),)).fetchall()]

 def record_tactical_decision(self, club_id, event_type, payload, match_id=None):
  if not str(event_type).strip(): raise ValueError('INVALID_TACTICAL_EVENT')
  if not self.connection.execute('SELECT 1 FROM player_sport_state WHERE club_id=? LIMIT 1',(int(club_id),)).fetchone(): raise ValueError('UNKNOWN_CLUB')
  encoded=json.dumps(payload if isinstance(payload,dict) else {'value':payload},ensure_ascii=False,sort_keys=True,separators=(',',':'))
  cursor=self.connection.execute('INSERT INTO tactical_decision_history(club_id,match_id,event_type,decision_date,payload) VALUES(?,?,?,?,?)',(int(club_id),None if match_id is None else int(match_id),str(event_type),date.today().isoformat(),encoded)); self.connection.commit()
  row=self.connection.execute('SELECT * FROM tactical_decision_history WHERE decision_id=?',(cursor.lastrowid,)).fetchone()
  result=dict(row); result['payload']=json.loads(result['payload']); return result

 def tactical_decision_history(self, club_id, match_id=None):
  query='SELECT * FROM tactical_decision_history WHERE club_id=?'; args=[int(club_id)]
  if match_id is not None: query+=' AND match_id=?'; args.append(int(match_id))
  query+=' ORDER BY decision_id ASC'
  return [dict(row, payload=json.loads(row['payload'])) for row in self.connection.execute(query,args).fetchall()]

 def position_coverage_alerts(self, club_id, minimum_available=2):
  minimum=int(minimum_available)
  if minimum < 0: raise ValueError('INVALID_POSITION_COVERAGE_THRESHOLD')
  report=self.squad_depth_report(club_id)
  alerts=tuple({'position_code':row['position_code'],'available':row['available'],'required':minimum,'covered':row['available'] >= minimum,'player_ids':tuple(row['player_ids'])} for row in report['positions'] if row['available'] < minimum)
  return {'club_id':int(club_id),'minimum_available':minimum,'alerts':alerts,'valid':not alerts}

 def calculate_chemistry(self, club_id, lineup_id=None):
  if lineup_id is None:
   lineup = self.connection.execute('SELECT lineup_id FROM lineups WHERE club_id=? ORDER BY lineup_id DESC LIMIT 1',(int(club_id),)).fetchone()
  else:
   lineup = self.connection.execute('SELECT lineup_id FROM lineups WHERE lineup_id=? AND club_id=?',(int(lineup_id),int(club_id))).fetchone()
  if not lineup:
   return {'club_id': int(club_id), 'lineup_id': None, 'score': 0, 'available_players': self.squad_summary(club_id)['available'], 'position_coverage': 0, 'valid': False}
  rows=self.connection.execute('SELECT lp.player_id,COALESCE(pp.position_code,lp.position_code) AS position_code,s.available,s.recovery_days FROM lineup_players lp JOIN lineups l ON l.lineup_id=lp.lineup_id LEFT JOIN player_positions pp ON pp.player_id=lp.player_id LEFT JOIN player_sport_state s ON s.player_id=lp.player_id WHERE lp.lineup_id=? ORDER BY lp.player_id',(int(lineup['lineup_id']),)).fetchall()
  if not rows:
   return {'club_id': int(club_id), 'lineup_id': int(lineup['lineup_id']), 'score': 0, 'available_players': 0, 'position_coverage': 0, 'valid': False}
  position_coverage=len({int(row['position_code']) for row in rows})
  available=sum(1 for row in rows if row['available'] and row['recovery_days']==0)
  score=round(100 * (0.55 * min(1, available/11) + 0.45 * min(1, position_coverage/5)))
  return {'club_id': int(club_id), 'lineup_id': int(lineup['lineup_id']), 'score': int(score), 'available_players': int(available), 'position_coverage': int(position_coverage), 'valid': bool(len(rows) >= 11 and available >= 11)}

 def calculate_morale_impact(self, club_id, lineup_id=None):
  chemistry=self.calculate_chemistry(club_id,lineup_id)
  if not chemistry['lineup_id']:
   return {'club_id': int(club_id), 'lineup_id': None, 'average_form': 0.0, 'average_fatigue': 0.0, 'modifier': 0.0, 'valid': False}
  rows=self.connection.execute('SELECT s.form,s.fatigue,s.available,s.recovery_days FROM lineup_players lp JOIN player_sport_state s ON s.player_id=lp.player_id WHERE lp.lineup_id=? ORDER BY lp.player_id',(chemistry['lineup_id'],)).fetchall()
  if not rows:
   return {'club_id': int(club_id), 'lineup_id': chemistry['lineup_id'], 'average_form': 0.0, 'average_fatigue': 0.0, 'modifier': 0.0, 'valid': False}
  average_form=sum(float(row['form']) for row in rows)/len(rows)
  average_fatigue=sum(float(row['fatigue']) for row in rows)/len(rows)
  modifier=round(max(-0.25,min(0.25,((average_form-50)/200)-((average_fatigue-50)/250)+(chemistry['score']-50)/500)),4)
  return {'club_id': int(club_id), 'lineup_id': chemistry['lineup_id'], 'average_form': round(average_form,2), 'average_fatigue': round(average_fatigue,2), 'modifier': modifier, 'valid': chemistry['valid']}

 def physical_condition(self, club_id, player_id=None):
  query='SELECT s.player_id,s.club_id,s.condition,s.fatigue,s.form,s.available,s.recovery_days FROM player_sport_state s WHERE s.club_id=?'; args=[int(club_id)]
  if player_id is not None: query+=' AND s.player_id=?'; args.append(int(player_id))
  rows=self.connection.execute(query,args).fetchall()
  if player_id is not None and not rows: raise ValueError('PLAYER_OUTSIDE_CLUB')
  result=[]
  for row in rows:
   condition=int(row['condition']); fatigue=int(row['fatigue']); injury=row['recovery_days']>0; suspended=self.is_suspended(row['player_id'])
   risk='CRITICAL' if injury or fatigue>=90 or condition<=20 else 'HIGH' if fatigue>=70 or condition<=40 else 'MEDIUM' if fatigue>=45 or condition<=60 else 'LOW'
   result.append({'player_id':int(row['player_id']),'club_id':int(row['club_id']),'condition':condition,'fatigue':fatigue,'form':int(row['form']),'available':self.is_available(row['player_id']),'recovery_days':int(row['recovery_days']),'suspended':suspended,'fatigue_risk':risk})
  return result

 def confirm_lineup(self, club_id, competition_id, lineup_id, match_id=None):
  lineup=self.connection.execute('SELECT lineup_id,club_id FROM lineups WHERE lineup_id=? AND club_id=?',(int(lineup_id),int(club_id))).fetchone()
  if not lineup: raise ValueError('LINEUP_OUTSIDE_CLUB')
  if int(competition_id) <= 0: raise ValueError('INVALID_COMPETITION')
  players=self.connection.execute('SELECT player_id FROM lineup_players WHERE lineup_id=? AND starter=1 ORDER BY player_id',(int(lineup_id),)).fetchall()
  if len(players) < 11: raise ValueError('INSUFFICIENT_LINEUP_PLAYERS')
  if any(not self.is_available(row['player_id']) for row in players): raise ValueError('LINEUP_HAS_UNAVAILABLE_PLAYER')
  if match_id is not None:
   table=self.connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='matches'").fetchone()
   if table:
    match=self.connection.execute('SELECT home_team_id,away_team_id FROM matches WHERE match_id=? AND competition_id=?',(int(match_id),int(competition_id))).fetchone()
    if not match: raise ValueError('MATCH_NOT_IN_COMPETITION')
    if int(club_id) not in (int(match['home_team_id']),int(match['away_team_id'])): raise ValueError('CLUB_NOT_IN_MATCH')
  now=date.today().isoformat()
  with self.connection:
   self.connection.execute('INSERT INTO lineup_history(club_id,lineup_id,event_type,created_at,payload) VALUES(?,?,?,?,?)',(int(club_id),int(lineup_id),'LINEUP_CONFIRMED',now,json.dumps({'competition_id':int(competition_id),'match_id':match_id},sort_keys=True,separators=(',',':'))))
   self.connection.execute('INSERT OR IGNORE INTO lineup_confirmations(club_id,competition_id,lineup_id,match_id,confirmed_at) VALUES(?,?,?,?,?)',(int(club_id),int(competition_id),int(lineup_id),None if match_id is None else int(match_id),now))
   self.connection.execute('INSERT INTO tactical_decision_history(club_id,match_id,event_type,decision_date,payload) VALUES(?,?,?,?,?)',(int(club_id),None if match_id is None else int(match_id),'LINEUP_CONFIRMED',now,json.dumps({'competition_id':int(competition_id),'lineup_id':int(lineup_id),'player_ids':[int(row['player_id']) for row in players]},sort_keys=True,separators=(',',':'))))
  row=self.connection.execute('SELECT * FROM lineup_confirmations WHERE club_id=? AND competition_id=? AND lineup_id=? AND (match_id IS ? OR match_id=?)',(int(club_id),int(competition_id),int(lineup_id),None if match_id is None else int(match_id),None if match_id is None else int(match_id))).fetchone()
  return dict(row)

 def lineup_history(self, club_id, lineup_id=None):
  query='SELECT * FROM lineup_history WHERE club_id=?'; args=[int(club_id)]
  if lineup_id is not None: query+=' AND lineup_id=?'; args.append(int(lineup_id))
  query+=' ORDER BY history_id'
  return [dict(row, payload=json.loads(row['payload'])) for row in self.connection.execute(query,args).fetchall()]

 def validate_minimum_lineup(self, club_id, minimum=11):
  available = self.squad_summary(club_id)['available']
  if available < minimum:
   raise ValueError(f'INSUFFICIENT_AVAILABLE_PLAYERS:{available}:{minimum}')
  return {'club_id': club_id, 'minimum': minimum, 'available': available, 'valid': True}
 def promote(self,player_id,to_category=SquadCategory.RESERVE):
  if to_category==SquadCategory.YOUTH: raise ValueError('promotion destination must be professional')
  row=self.connection.execute('select * from player_sport_state where player_id=?',(player_id,)).fetchone()
  if not row: raise KeyError(player_id)
  self.connection.execute('update player_sport_state set category=?,last_updated=? where player_id=?',(to_category.value,date.today().isoformat(),player_id)); self.connection.execute('insert into sport_history(player_id,event_type,event_date,payload) values(?,?,?,?)',(player_id,'PLAYER_PROMOTED',date.today().isoformat(),to_category.value)); self.connection.commit()
 def train(self,player_id,training=TrainingType.GENERAL,load=10,seed=None):
  row=self.connection.execute('select * from player_sport_state where player_id=?',(player_id,)).fetchone()
  if not row: raise KeyError(player_id)
  load=max(0,min(100,load)); rng=random.Random(seed); delta=rng.randint(0,2); fatigue=min(100,row['fatigue']+load); form=max(0,min(100,row['form']+delta-(1 if fatigue>80 else 0))); available=0 if fatigue>=100 else row['available']
  self.connection.execute('update player_sport_state set training=?,fatigue=?,form=?,available=?,last_updated=? where player_id=?',(training.value if hasattr(training,'value') else training,fatigue,form,available,date.today().isoformat(),player_id)); self.connection.commit()
 def rest(self,player_id,amount=10):
  self.connection.execute('update player_sport_state set fatigue=max(0,fatigue-?),available=case when recovery_days=0 then 1 else available end,last_updated=? where player_id=?',(amount,date.today().isoformat(),player_id)); self.connection.commit()
 def injure(self,player_id,injury_type='muscular',days=7,seed=None):
  if days<=0: raise ValueError('invalid injury duration')
  with self.connection:
   end=date.fromordinal(date.today().toordinal()+days).isoformat(); cur=self.connection.execute('insert into injuries(player_id,injury_type,start_date,estimated_days,end_date,severity,status) values(?,?,?,?,?,?,?)',(player_id,injury_type,date.today().isoformat(),days,end,'minor' if days<15 else 'moderate',InjuryStatus.ACTIVE.value)); iid=cur.lastrowid; self.connection.execute('update player_sport_state set available=0,current_injury_id=?,recovery_days=?,last_updated=? where player_id=?',(iid,days,date.today().isoformat(),player_id)); return int(iid)
 def recover(self,player_id,days=1):
  row=self.connection.execute('select * from player_sport_state where player_id=?',(player_id,)).fetchone()
  if not row: raise KeyError(player_id)
  remaining=max(0,row['recovery_days']-days); avail=1 if remaining==0 else 0; self.connection.execute('update player_sport_state set recovery_days=?,available=?,last_updated=? where player_id=?',(remaining,avail,date.today().isoformat(),player_id));
  if remaining==0 and row['current_injury_id']: self.connection.execute('update injuries set status=? where injury_id=?',(InjuryStatus.RECOVERED.value,row['current_injury_id']))
  self.connection.commit()
 def suspend(self, player_id, days, reason='disciplinar'):
  if int(days) <= 0 or not str(reason).strip(): raise ValueError('INVALID_SUSPENSION')
  if not self.connection.execute('SELECT 1 FROM player_sport_state WHERE player_id=?',(int(player_id),)).fetchone(): raise KeyError(player_id)
  until=date.fromordinal(date.today().toordinal()+int(days)).isoformat()
  self.connection.execute('INSERT INTO player_suspensions(player_id,until_date,reason,active,created_at) VALUES(?,?,?,?,?) ON CONFLICT(player_id) DO UPDATE SET until_date=excluded.until_date,reason=excluded.reason,active=1',(int(player_id),until,str(reason).strip(),1,date.today().isoformat())); self.connection.commit()
  return dict(self.connection.execute('SELECT * FROM player_suspensions WHERE player_id=?',(int(player_id),)).fetchone())

 def is_suspended(self, player_id):
  row=self.connection.execute('SELECT active,until_date FROM player_suspensions WHERE player_id=?',(int(player_id),)).fetchone()
  return bool(row and row['active'] and row['until_date'] >= date.today().isoformat())

 def is_available(self,player_id):
  r=self.connection.execute('select available,club_id,recovery_days from player_sport_state where player_id=?',(player_id,)).fetchone(); return bool(r and r['available'] and r['club_id'] is not None and r['recovery_days']==0 and not self.is_suspended(player_id))
 def auto_lineup(self, club_id, formation='4-3-3'):
  if not formation or '-' not in formation: raise ValueError('invalid formation')
  self.validate_minimum_lineup(club_id, minimum=11)
  rows=self.connection.execute("SELECT s.player_id,s.form,p.position_code FROM player_sport_state s LEFT JOIN player_positions p ON p.player_id=s.player_id WHERE s.club_id=? AND s.available=1 AND s.recovery_days=0 AND NOT EXISTS (SELECT 1 FROM player_suspensions ps WHERE ps.player_id=s.player_id AND ps.active=1 AND ps.until_date>=date('now')) ORDER BY COALESCE(p.position_code,3),s.form DESC,s.player_id",(club_id,)).fetchall()
  selected=[]; used=set()
  for position in range(1,12):
   candidate=next((row for row in rows if row['player_id'] not in used and int(row['position_code'] or 3) == position),None)
   if candidate: selected.append(int(candidate['player_id'])); used.add(int(candidate['player_id']))
  for row in rows:
   if len(selected) >= 11: break
   if row['player_id'] not in used: selected.append(int(row['player_id'])); used.add(int(row['player_id']))
  if len(selected) < 11: raise ValueError(f'INSUFFICIENT_AVAILABLE_PLAYERS:{len(selected)}:11')
  return self.create_lineup(club_id, formation, selected[:11])

 def save_formation(self, club_id, competition_id, name, formation, players):
  if int(competition_id) <= 0 or not str(name).strip(): raise ValueError('INVALID_SAVED_FORMATION')
  ids=[int(x[0]) if isinstance(x,(tuple,list)) else int(x) for x in players]
  if len(ids)!=len(set(ids)) or not formation or '-' not in formation: raise ValueError('INVALID_SAVED_FORMATION')
  for pid in ids:
   row=self.connection.execute('select club_id from player_sport_state where player_id=?',(pid,)).fetchone()
   if not row or row['club_id'] != club_id or not self.is_available(pid): raise ValueError('player unavailable or outside club')
  now=date.today().isoformat()
  with self.connection:
   self.connection.execute('INSERT INTO saved_formations(club_id,competition_id,name,formation,created_at,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(club_id,competition_id,name) DO UPDATE SET formation=excluded.formation,updated_at=excluded.updated_at',(club_id,competition_id,str(name).strip(),formation,now,now))
   saved=self.connection.execute('SELECT saved_formation_id FROM saved_formations WHERE club_id=? AND competition_id=? AND name=?',(club_id,competition_id,str(name).strip())).fetchone()
   self.connection.execute('DELETE FROM saved_formation_players WHERE saved_formation_id=?',(saved['saved_formation_id'],))
   self.connection.executemany('INSERT INTO saved_formation_players(saved_formation_id,player_id,position_code,starter) VALUES(?,?,?,1)',[(saved['saved_formation_id'],pid,3) for pid in ids])
  return self.saved_formation(club_id, competition_id, name)

 def saved_formations(self, club_id, competition_id):
  rows=self.connection.execute('SELECT * FROM saved_formations WHERE club_id=? AND competition_id=? ORDER BY name',(club_id,competition_id)).fetchall()
  return [self._saved_formation_dict(row) for row in rows]

 def saved_formation(self, club_id, competition_id, name):
  row=self.connection.execute('SELECT * FROM saved_formations WHERE club_id=? AND competition_id=? AND name=?',(club_id,competition_id,str(name).strip())).fetchone()
  if not row: raise KeyError(name)
  return self._saved_formation_dict(row)

 def _saved_formation_dict(self, row):
  players=self.connection.execute('SELECT player_id,position_code,starter FROM saved_formation_players WHERE saved_formation_id=? ORDER BY player_id',(row['saved_formation_id'],)).fetchall()
  return {'saved_formation_id':int(row['saved_formation_id']),'club_id':int(row['club_id']),'competition_id':int(row['competition_id']),'name':row['name'],'formation':row['formation'],'player_ids':tuple(int(player['player_id']) for player in players),'players':tuple(dict(player) for player in players)}

 def create_match_lineup(self, club_id, competition_id, name):
  saved=self.saved_formation(club_id, competition_id, name)
  self.validate_minimum_lineup(club_id, minimum=11)
  if len(saved['player_ids']) < 11: raise ValueError('INSUFFICIENT_SAVED_FORMATION_PLAYERS')
  return self.create_lineup(club_id, saved['formation'], saved['player_ids'])

 def create_lineup(self,club_id,formation,players):
  ids=[int(x[0]) if isinstance(x,(tuple,list)) else int(x) for x in players]
  if len(ids)!=len(set(ids)): raise ValueError('duplicate player in lineup')
  if not formation or '-' not in formation: raise ValueError('invalid formation')
  for pid in ids:
   r=self.connection.execute('select club_id from player_sport_state where player_id=?',(pid,)).fetchone()
   if not r or r['club_id']!=club_id or not self.is_available(pid): raise ValueError('player unavailable or outside club')
  cur=self.connection.execute('insert into lineups(club_id,formation,created_at) values(?,?,?)',(club_id,formation,date.today().isoformat())); lid=cur.lastrowid
  for pid in ids: self.connection.execute('insert into lineup_players(lineup_id,player_id,position_code,starter) values(?,?,?,1)',(lid,pid,3))
  self.connection.commit(); return Lineup(int(lid),club_id,formation,tuple(ids))
 def record_player_match_stats(self, match_id, player_id, minutes=0, goals=0, assists=0, cards=0, rating=None):
  values=(int(minutes),int(goals),int(assists),int(cards))
  if int(match_id) <= 0 or int(player_id) <= 0 or any(value < 0 for value in values) or values[0] > 120 or (rating is not None and not 0 <= float(rating) <= 10): raise ValueError('INVALID_PLAYER_MATCH_STATS')
  self.connection.execute('INSERT INTO player_match_stats(match_id,player_id,minutes,goals,assists,cards,rating) VALUES(?,?,?,?,?,?,?) ON CONFLICT(match_id,player_id) DO UPDATE SET minutes=excluded.minutes,goals=excluded.goals,assists=excluded.assists,cards=excluded.cards,rating=excluded.rating',(int(match_id),int(player_id),*values,rating)); self.connection.commit()
  return dict(self.connection.execute('SELECT * FROM player_match_stats WHERE match_id=? AND player_id=?',(int(match_id),int(player_id))).fetchone())

 def player_match_stats(self, match_id):
  return [dict(row) for row in self.connection.execute('SELECT * FROM player_match_stats WHERE match_id=? ORDER BY player_id',(int(match_id),)).fetchall()]

 def sync_cards_from_events(self, match_id):
  events=self.connection.execute("SELECT player_id,payload FROM match_events WHERE match_id=? AND event_type IN ('YELLOW_CARD','RED_CARD','CARD') AND player_id IS NOT NULL ORDER BY event_id",(int(match_id),)).fetchall()
  counts={}
  for event in events:
   counts[int(event['player_id'])]=counts.get(int(event['player_id']),0)+1
  with self.connection:
   for player_id,cards in counts.items():
    self.connection.execute('INSERT INTO player_match_stats(match_id,player_id,cards) VALUES(?,?,?) ON CONFLICT(match_id,player_id) DO UPDATE SET cards=excluded.cards',(int(match_id),player_id,cards))
  return self.player_match_stats(match_id)

 def player_season_totals(self, player_id=None, match_ids=None):
  clauses=[]; params=[]
  if player_id is not None: clauses.append('player_id=?'); params.append(int(player_id))
  if match_ids:
   marks=','.join('?' for _ in match_ids); clauses.append(f'match_id IN ({marks})'); params.extend(int(value) for value in match_ids)
  where=(' WHERE ' + ' AND '.join(clauses)) if clauses else ''
  rows=self.connection.execute(f'''SELECT player_id,SUM(minutes) AS minutes,SUM(goals) AS goals,SUM(assists) AS assists,SUM(cards) AS cards,COUNT(*) AS appearances,AVG(rating) AS average_rating FROM player_match_stats{where} GROUP BY player_id ORDER BY goals DESC,assists DESC,minutes DESC,player_id''',params).fetchall()
  return [dict(row) for row in rows]

 def plan_substitution(self, lineup_id, minute_target, outgoing_player_id, incoming_player_id):
  minute=int(minute_target)
  if minute < 1 or minute > 120 or int(outgoing_player_id) == int(incoming_player_id): raise ValueError('INVALID_SUBSTITUTION_PLAN')
  lineup=self.connection.execute('SELECT club_id FROM lineups WHERE lineup_id=?',(lineup_id,)).fetchone()
  if not lineup: raise KeyError(lineup_id)
  outgoing=self.connection.execute('SELECT 1 FROM lineup_players WHERE lineup_id=? AND player_id=? AND starter=1',(lineup_id,outgoing_player_id)).fetchone()
  if not outgoing: raise ValueError('OUTGOING_PLAYER_NOT_IN_LINEUP')
  incoming=self.connection.execute('SELECT club_id,available,recovery_days FROM player_sport_state WHERE player_id=?',(incoming_player_id,)).fetchone()
  if not incoming or incoming['club_id'] != lineup['club_id'] or not incoming['available'] or incoming['recovery_days'] > 0: raise ValueError('INCOMING_PLAYER_UNAVAILABLE')
  now=date.today().isoformat()
  with self.connection:
   self.connection.execute('INSERT INTO substitution_plans(lineup_id,minute_target,outgoing_player_id,incoming_player_id,status,created_at) VALUES(?,?,?,?,?,?) ON CONFLICT(lineup_id,minute_target,outgoing_player_id) DO UPDATE SET incoming_player_id=excluded.incoming_player_id,status=excluded.status',(lineup_id,minute,outgoing_player_id,incoming_player_id,'PLANNED',now))
  return self.planned_substitutions(lineup_id)[-1]

 def planned_substitutions(self, lineup_id):
  rows=self.connection.execute('SELECT * FROM substitution_plans WHERE lineup_id=? ORDER BY minute_target,plan_id',(lineup_id,)).fetchall()
  return [dict(row) for row in rows]

 def apply_substitution(self, plan_id, minute, match_id=None):
  minute=int(minute)
  plan=self.connection.execute('SELECT * FROM substitution_plans WHERE plan_id=?',(plan_id,)).fetchone()
  if not plan: raise KeyError(plan_id)
  if plan['status'] == 'APPLIED': return dict(plan)
  if minute < int(plan['minute_target']) or minute > 120: raise ValueError('INVALID_SUBSTITUTION_MINUTE')
  outgoing=self.connection.execute('SELECT position_code FROM lineup_players WHERE lineup_id=? AND player_id=? AND starter=1',(plan['lineup_id'],plan['outgoing_player_id'])).fetchone()
  incoming=self.connection.execute('SELECT 1 FROM lineup_players WHERE lineup_id=? AND player_id=?',(plan['lineup_id'],plan['incoming_player_id'])).fetchone()
  if not outgoing: raise ValueError('OUTGOING_PLAYER_NOT_ACTIVE')
  if incoming: raise ValueError('INCOMING_PLAYER_ALREADY_IN_LINEUP')
  with self.connection:
   self.connection.execute('UPDATE lineup_players SET starter=0 WHERE lineup_id=? AND player_id=?',(plan['lineup_id'],plan['outgoing_player_id']))
   self.connection.execute('INSERT INTO lineup_players(lineup_id,player_id,position_code,starter) VALUES(?,?,?,1)',(plan['lineup_id'],plan['incoming_player_id'],outgoing['position_code']))
   self.connection.execute("UPDATE substitution_plans SET status='APPLIED',applied_minute=? WHERE plan_id=?",(minute,plan_id))
   if match_id is not None:
    self.connection.execute('UPDATE player_match_stats SET minutes=? WHERE match_id=? AND player_id=?',(minute,int(match_id),plan['outgoing_player_id']))
    self.connection.execute('INSERT INTO player_match_stats(match_id,player_id,minutes,goals,assists,cards,rating) VALUES(?,?,?,?,?,?,?) ON CONFLICT(match_id,player_id) DO UPDATE SET minutes=excluded.minutes',(int(match_id),plan['incoming_player_id'],120-minute,0,0,0,7.0))
  return dict(self.connection.execute('SELECT * FROM substitution_plans WHERE plan_id=?',(plan_id,)).fetchone())

 def team_strength(self,lineup_id):
  rows=self.connection.execute('select s.* from player_sport_state s join lineup_players l on l.player_id=s.player_id where l.lineup_id=?',(lineup_id,)).fetchall();
  if not rows:return 0.0
  return sum((50+row['form']*.3-row['fatigue']*.2) for row in rows if row['available'])/len(rows)
 def close(self): self.connection.close()
