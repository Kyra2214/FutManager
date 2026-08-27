from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
import random,sqlite3
from contextlib import nullcontext
from engine.world.time_and_finance import FinanceLedger,WorldTickContext,LogicalClock
from engine.core.state_store import assert_mutable_state_path
SCHEMA='''
CREATE TABLE IF NOT EXISTS club_stadiums(stadium_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,name TEXT NOT NULL,capacity INTEGER NOT NULL,usable_capacity INTEGER NOT NULL,state INTEGER NOT NULL DEFAULT 100,level INTEGER NOT NULL DEFAULT 1,comfort INTEGER NOT NULL DEFAULT 50,security INTEGER NOT NULL DEFAULT 50,quality INTEGER NOT NULL DEFAULT 50,maintenance_cost INTEGER NOT NULL DEFAULT 0,construction_date TEXT NOT NULL,last_maintenance TEXT,status TEXT NOT NULL DEFAULT 'ACTIVE',is_primary INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS club_fan_base(club_id INTEGER PRIMARY KEY,size INTEGER NOT NULL DEFAULT 0,loyalty INTEGER NOT NULL DEFAULT 50,satisfaction INTEGER NOT NULL DEFAULT 50,growth INTEGER NOT NULL DEFAULT 0,interest INTEGER NOT NULL DEFAULT 50,engagement INTEGER NOT NULL DEFAULT 50,local_reputation INTEGER NOT NULL DEFAULT 50,national_reputation INTEGER NOT NULL DEFAULT 50,international_reputation INTEGER NOT NULL DEFAULT 20,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS club_reputation(club_id INTEGER PRIMARY KEY,sporting INTEGER NOT NULL DEFAULT 50,national INTEGER NOT NULL DEFAULT 50,international INTEGER NOT NULL DEFAULT 20,commercial INTEGER NOT NULL DEFAULT 30,historical INTEGER NOT NULL DEFAULT 20,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS attendance_records(attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,match_id INTEGER NOT NULL UNIQUE,club_id INTEGER NOT NULL,expected_attendance INTEGER NOT NULL,actual_attendance INTEGER NOT NULL,occupancy_rate REAL NOT NULL,ticket_price INTEGER NOT NULL,revenue INTEGER NOT NULL,seed INTEGER);
CREATE TABLE IF NOT EXISTS club_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,type TEXT NOT NULL,origin TEXT,severity INTEGER NOT NULL,event_date TEXT NOT NULL,title TEXT NOT NULL,description TEXT,impact TEXT,status TEXT NOT NULL DEFAULT 'OPEN',reference TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS stadium_history(history_id INTEGER PRIMARY KEY AUTOINCREMENT,stadium_id INTEGER NOT NULL,event_type TEXT NOT NULL,event_date TEXT NOT NULL,payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS club_social_history(history_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,source_type TEXT NOT NULL,source_id TEXT NOT NULL,fan_size_before INTEGER NOT NULL,fan_size_after INTEGER NOT NULL,satisfaction_before INTEGER NOT NULL,satisfaction_after INTEGER NOT NULL,sporting_before INTEGER NOT NULL,sporting_after INTEGER NOT NULL,commercial_before INTEGER NOT NULL,commercial_after INTEGER NOT NULL,event_date TEXT NOT NULL,UNIQUE(club_id,source_type,source_id));
CREATE TABLE IF NOT EXISTS club_reputation_history(history_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,source_type TEXT NOT NULL,source_id TEXT NOT NULL,sporting_before INTEGER NOT NULL,sporting_after INTEGER NOT NULL,commercial_before INTEGER NOT NULL,commercial_after INTEGER NOT NULL,event_date TEXT NOT NULL,UNIQUE(club_id,source_type,source_id));
'''
@dataclass(frozen=True)
class Attendance: expected:int; actual:int; occupancy:float; revenue:int
class SocialService:
 def __init__(self,db):
  assert_mutable_state_path(db) if not isinstance(db,sqlite3.Connection) else None;self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db;self.connection.row_factory=sqlite3.Row;self.connection.execute('PRAGMA foreign_keys=ON');self.connection.executescript(SCHEMA);self.connection.commit();LogicalClock(self.connection);self.ledger=FinanceLedger(self.connection)
 def create_stadium(self,club_id,name,capacity,comfort=50,security=50,quality=50,cost=0):
  if capacity<=0:raise ValueError('INVALID_CAPACITY')
  if self.connection.execute("select 1 from club_stadiums where club_id=? and is_primary=1 and status='ACTIVE'",(club_id,)).fetchone():raise ValueError('PRIMARY_STADIUM_EXISTS')
  cur=self.connection.execute('insert into club_stadiums(club_id,name,capacity,usable_capacity,comfort,security,quality,maintenance_cost,construction_date,last_maintenance) values(?,?,?,?,?,?,?,?,?,?)',(club_id,name,capacity,capacity,comfort,security,quality,cost,date.today().isoformat(),date.today().isoformat()));self.connection.commit();return int(cur.lastrowid)
 def upgrade(self,stadium_id,attribute,value,cost,context):
  if attribute not in ('capacity','comfort','security','quality') or value<=0:raise ValueError('INVALID_UPGRADE')
  with self.connection:
   r=self.connection.execute('select club_id from club_stadiums where stadium_id=?',(stadium_id,)).fetchone()
   if not r:raise KeyError(stadium_id)
   self.ledger.post(context,r[0],'EXPENSE','FACILITY',-cost,'stadium',str(stadium_id),'Stadium upgrade');self.connection.execute(f'update club_stadiums set {attribute}={attribute}+?,usable_capacity=case when ?="capacity" then capacity+? else usable_capacity end where stadium_id=?',(value,attribute,value,stadium_id));self.connection.execute('insert into stadium_history(stadium_id,event_type,event_date,payload) values(?,?,?,?)',(stadium_id,'UPGRADE_COMPLETED',context.current_date.isoformat(),f'{attribute}:{value}'))
 def ensure_fan_reputation(self,club_id,size=1000,managed_transaction=True):
  now=date.today().isoformat();self.connection.execute('insert or ignore into club_fan_base(club_id,size,updated_at) values(?,?,?)',(club_id,size,now));self.connection.execute('insert or ignore into club_reputation(club_id,updated_at) values(?,?)',(club_id,now));
  if managed_transaction:self.connection.commit()
 def attendance(self,match_id,club_id,context,visitor_reputation=30,importance=50,ticket_price=20,seed=None):
  if self.connection.execute('select 1 from attendance_records where match_id=?',(match_id,)).fetchone():
   r=self.connection.execute('select expected_attendance,actual_attendance,occupancy_rate,revenue from attendance_records where match_id=?',(match_id,)).fetchone(); return Attendance(r[0],r[1],r[2],r[3])
  stadium=self.connection.execute("select * from club_stadiums where club_id=? and status='ACTIVE' order by is_primary desc limit 1",(club_id,)).fetchone();fans=self.connection.execute('select * from club_fan_base where club_id=?',(club_id,)).fetchone();rep=self.connection.execute('select * from club_reputation where club_id=?',(club_id,)).fetchone()
  cap=stadium['usable_capacity'] if stadium else 1000; base=fans['size'] if fans else 1000; score=.25+(fans['satisfaction'] if fans else 50)/200+(rep['commercial'] if rep else 30)/300+importance/400+visitor_reputation/500;expected=min(cap,max(0,int(base*score)));actual=min(cap,max(0,int(expected*(.9+random.Random(seed).random()*.2))));occ=actual/cap;rev=actual*ticket_price
  self.connection.execute('insert into attendance_records(match_id,club_id,expected_attendance,actual_attendance,occupancy_rate,ticket_price,revenue,seed) values(?,?,?,?,?,?,?,?)',(match_id,club_id,expected,actual,occ,ticket_price,rev,seed));self.connection.commit();return Attendance(expected,actual,occ,rev)
 def record_matchday_revenue(self,match_id,context):
  r=self.connection.execute('select * from attendance_records where match_id=?',(match_id,)).fetchone();
  if not r:raise KeyError(match_id)
  self.ledger.post(context,r['club_id'],'INCOME','MATCHDAY',r['revenue'],'attendance',str(match_id),'Bilheteria');return r['revenue']
 def event(self,club_id,type_,title,description='',severity=1,reference=None,origin='service'):
  self.connection.execute('insert or ignore into club_events(club_id,type,origin,severity,event_date,title,description,reference) values(?,?,?,?,?,?,?,?)',(club_id,type_,origin,severity,date.today().isoformat(),title,description,reference));self.connection.commit()
 def update_reputation(self,club_id,sporting_delta=0,commercial_delta=0,source_type='manual',source_id=None,managed_transaction=True):
  r=self.connection.execute('select * from club_reputation where club_id=?',(club_id,)).fetchone();
  if not r:self.ensure_fan_reputation(club_id,managed_transaction=managed_transaction);r=self.connection.execute('select * from club_reputation where club_id=?',(club_id,)).fetchone()
  def clamp(v):return max(0,min(100,v))
  source_id=str(source_id or f'{source_type}:{date.today().isoformat()}')
  sporting_after=clamp(r['sporting']+sporting_delta);commercial_after=clamp(r['commercial']+commercial_delta)
  with (self.connection if managed_transaction else nullcontext()):
   self.connection.execute('update club_reputation set sporting=?,commercial=?,national=?,updated_at=? where club_id=?',(sporting_after,commercial_after,clamp(r['national']+sporting_delta//2),date.today().isoformat(),club_id))
   self.connection.execute('insert or ignore into club_reputation_history(club_id,source_type,source_id,sporting_before,sporting_after,commercial_before,commercial_after,event_date) values(?,?,?,?,?,?,?,?)',(club_id,source_type,source_id,r['sporting'],sporting_after,r['commercial'],commercial_after,date.today().isoformat()))
  return {'status':'UPDATED','sporting_before':r['sporting'],'sporting_after':sporting_after,'commercial_before':r['commercial'],'commercial_after':commercial_after,'source_type':source_type,'source_id':source_id}
 def apply_match_result(self,match_id,club_id,goals_for,goals_against,importance=50,managed_transaction=True):
  """Atualização gradual, idempotente e derivada de uma partida já persistida."""
  self.ensure_fan_reputation(club_id,managed_transaction=managed_transaction)
  existing=self.connection.execute("select 1 from club_social_history where club_id=? and source_type='match' and source_id=?",(club_id,str(match_id))).fetchone()
  if existing:return {'status':'ALREADY_PROCESSED'}
  fan=self.connection.execute('select * from club_fan_base where club_id=?',(club_id,)).fetchone();rep=self.connection.execute('select * from club_reputation where club_id=?',(club_id,)).fetchone()
  result=1 if goals_for>goals_against else 0 if goals_for==goals_against else -1
  scale=max(1,min(3,int(importance)//35+1)); satisfaction_delta=result*scale
  sporting_delta=result*scale
  commercial_delta=1 if result>0 and importance>=70 else 0
  clamp=lambda value:max(0,min(100,int(value)))
  satisfaction_after=clamp(fan['satisfaction']+satisfaction_delta); engagement_after=clamp(fan['engagement']+(1 if result>0 else -1 if result<0 else 0)); interest_after=clamp(fan['interest']+(1 if result>0 else 0))
  size_delta=max(-max(1,int(fan['size'])//250),min(max(1,int(fan['size'])//200),round((satisfaction_after-50)*max(1,int(fan['size']))/5000)))
  size_after=max(0,int(fan['size'])+size_delta); sporting_after=clamp(rep['sporting']+sporting_delta);commercial_after=clamp(rep['commercial']+commercial_delta)
  with (self.connection if managed_transaction else nullcontext()):
   self.connection.execute('update club_fan_base set size=?,satisfaction=?,engagement=?,interest=?,growth=?,updated_at=? where club_id=?',(size_after,satisfaction_after,engagement_after,interest_after,size_delta,date.today().isoformat(),club_id))
   self.connection.execute('update club_reputation set sporting=?,commercial=?,national=?,updated_at=? where club_id=?',(sporting_after,commercial_after,clamp(rep['national']+sporting_delta//2),date.today().isoformat(),club_id))
   self.connection.execute('insert into club_social_history(club_id,source_type,source_id,fan_size_before,fan_size_after,satisfaction_before,satisfaction_after,sporting_before,sporting_after,commercial_before,commercial_after,event_date) values(?,?,?,?,?,?,?,?,?,?,?,?)',(club_id,'match',str(match_id),fan['size'],size_after,fan['satisfaction'],satisfaction_after,rep['sporting'],sporting_after,rep['commercial'],commercial_after,date.today().isoformat()))
  return {'status':'UPDATED','satisfaction_delta':satisfaction_delta,'sporting_delta':sporting_delta,'fan_size_delta':size_delta}
 def ticket_price_preview(self,club_id,new_price,importance=50,visitor_reputation=30):
  if new_price<=0:raise ValueError('INVALID_TICKET_PRICE')
  stadium=self.connection.execute("select usable_capacity from club_stadiums where club_id=? and status='ACTIVE' order by is_primary desc limit 1",(club_id,)).fetchone();fans=self.connection.execute('select * from club_fan_base where club_id=?',(club_id,)).fetchone();rep=self.connection.execute('select * from club_reputation where club_id=?',(club_id,)).fetchone()
  cap=stadium['usable_capacity'] if stadium else 1000;base=fans['size'] if fans else 1000;satisfaction=fans['satisfaction'] if fans else 50;commercial=rep['commercial'] if rep else 30
  rejection=max(0,min(90,int(new_price/2-(satisfaction+commercial/2))))
  expected=max(0,min(cap,int(base*(.25+satisfaction/200+commercial/300+importance/400+visitor_reputation/500)*(1-rejection/100))))
  return {'club_id':club_id,'ticket_price':int(new_price),'expected_attendance':expected,'expected_revenue':expected*int(new_price),'rejection_risk':rejection,'persisted':False,'formula_version':'ticket-price-v1'}
 def fan_segments(self,club_id):
  row=self.connection.execute('select * from club_fan_base where club_id=?',(club_id,)).fetchone()
  if not row:return {'club_id':club_id,'segments':{'local':0,'national':0,'international':0},'source':'SQL'}
  size=int(row['size']);local=int(size*.65);national=int(size*.25);return {'club_id':club_id,'segments':{'local':local,'national':national,'international':size-local-national},'source':'club_fan_base'}
 def social_timeline(self,club_id,limit=25,offset=0):
  limit=max(1,min(100,int(limit)));offset=max(0,int(offset))
  rows=self.connection.execute('select history_id,source_type,source_id,fan_size_before,fan_size_after,satisfaction_before,satisfaction_after,sporting_before,sporting_after,commercial_before,commercial_after,event_date from club_social_history where club_id=? order by history_id desc limit ? offset ?',(club_id,limit,offset)).fetchall()
  return {'club_id':club_id,'items':[dict(row) for row in rows],'limit':limit,'offset':offset,'source':'club_social_history'}
 def close(self):self.connection.close()
