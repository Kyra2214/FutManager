from __future__ import annotations
from datetime import date
from enum import StrEnum
import sqlite3,json
from engine.core.schema import ensure_schema_version
from engine.core.state_store import assert_mutable_state_path, configure_state_connection
SCHEMA='''
CREATE TABLE IF NOT EXISTS managers(manager_id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,nationality TEXT,age INTEGER NOT NULL,reputation INTEGER NOT NULL DEFAULT 0,experience INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'ACTIVE',created_at TEXT NOT NULL,current_club_id INTEGER,active_career INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS manager_careers(career_id INTEGER PRIMARY KEY AUTOINCREMENT,manager_id INTEGER NOT NULL UNIQUE,name TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,season_id INTEGER,current_club_id INTEGER,status TEXT NOT NULL DEFAULT 'ACTIVE',engine_version TEXT NOT NULL DEFAULT '1.0');
CREATE TABLE IF NOT EXISTS manager_contracts(manager_contract_id INTEGER PRIMARY KEY AUTOINCREMENT,manager_id INTEGER NOT NULL,club_id INTEGER NOT NULL,start_date TEXT NOT NULL,end_date TEXT NOT NULL,salary INTEGER NOT NULL,bonus INTEGER NOT NULL DEFAULT 0,objective TEXT,status TEXT NOT NULL DEFAULT 'ACTIVE');
CREATE TABLE IF NOT EXISTS manager_objectives(objective_id INTEGER PRIMARY KEY AUTOINCREMENT,career_id INTEGER NOT NULL,type TEXT NOT NULL,priority INTEGER NOT NULL,deadline TEXT,status TEXT NOT NULL DEFAULT 'ACTIVE',progress REAL NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS manager_history(history_id INTEGER PRIMARY KEY AUTOINCREMENT,manager_id INTEGER NOT NULL,club_id INTEGER,event_type TEXT NOT NULL,event_date TEXT NOT NULL,payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS manager_inbox(message_id INTEGER PRIMARY KEY AUTOINCREMENT,manager_id INTEGER NOT NULL,type TEXT NOT NULL,title TEXT NOT NULL,body TEXT,reference TEXT UNIQUE,read INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS manager_job_offers(offer_id INTEGER PRIMARY KEY AUTOINCREMENT,manager_id INTEGER NOT NULL,club_id INTEGER NOT NULL,salary INTEGER NOT NULL,duration INTEGER NOT NULL,objective TEXT,reputation_min INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'OFFERED');
CREATE TABLE IF NOT EXISTS manager_selection_assignments(selection_assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,manager_id INTEGER NOT NULL UNIQUE,career_id INTEGER NOT NULL UNIQUE,selection_id INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'ACTIVE',appointed_at TEXT NOT NULL);
'''
class ManagerStatus(StrEnum): ACTIVE='ACTIVE'; RESIGNED='RESIGNED'; TERMINATED='TERMINATED'
class ManagerService:
 def __init__(self,db):
  if not isinstance(db,sqlite3.Connection): assert_mutable_state_path(db)
  self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db;configure_state_connection(self.connection);self.connection.executescript(SCHEMA);ensure_schema_version(self.connection);self.connection.commit()
 def create_manager(self,name,nationality,age):
  cur=self.connection.execute('insert into managers(name,nationality,age,created_at) values(?,?,?,?)',(name,nationality,age,date.today().isoformat()));self.connection.commit();return int(cur.lastrowid)
 def create_career(self,manager_id,name='Carreira',club_id=None,season_id=None):
  if self.connection.execute("select 1 from manager_careers where manager_id=? and status='ACTIVE'",(manager_id,)).fetchone():raise ValueError('ACTIVE_CAREER_EXISTS')
  cur=self.connection.execute('insert into manager_careers(manager_id,name,created_at,updated_at,season_id,current_club_id) values(?,?,?,?,?,?)',(manager_id,name,date.today().isoformat(),date.today().isoformat(),season_id,club_id));cid=int(cur.lastrowid);self.connection.execute('update managers set current_club_id=?,active_career=1 where manager_id=?',(club_id,manager_id));self.connection.commit();return cid
 def start_career(self,manager_name,nationality,age,career_name='Carreira',target_type='club',target_id=None,season_id=None):
  manager_name=(manager_name or '').strip();career_name=(career_name or 'Carreira').strip() or 'Carreira';age=int(age)
  if not manager_name:raise ValueError('MANAGER_NAME_REQUIRED')
  if age<18:raise ValueError('MANAGER_AGE_INVALID')
  if target_type not in ('club','selection'):raise ValueError('CAREER_TARGET_INVALID')
  if target_id is None:raise ValueError('CAREER_TARGET_REQUIRED')
  target_id=int(target_id)
  if self.connection.execute("select 1 from manager_careers where status='ACTIVE'").fetchone():raise ValueError('ACTIVE_CAREER_EXISTS')
  if target_type=='club' and not self.connection.execute('select 1 from times where time_id=?',(target_id,)).fetchone():raise ValueError('CLUB_NOT_FOUND')
  if target_type=='selection' and not self.connection.execute('select 1 from selecoes where selecao_id=?',(target_id,)).fetchone():raise ValueError('SELECTION_NOT_FOUND')
  today=date.today().isoformat();club_id=target_id if target_type=='club' else None
  if club_id is not None:
   from engine.economy.staff_market import StaffMarketService
   from engine.economy.sponsorships import SponsorshipService
   StaffMarketService(self.connection).bootstrap_club(club_id)
   SponsorshipService(self.connection).bootstrap_club(club_id)
  with self.connection:
   mid=int(self.connection.execute('insert into managers(name,nationality,age,created_at,current_club_id,active_career) values(?,?,?,?,?,1)',(manager_name,nationality or None,age,today,club_id)).lastrowid)
   cid=int(self.connection.execute('insert into manager_careers(manager_id,name,created_at,updated_at,season_id,current_club_id,status) values(?,?,?,?,?,?,?)',(mid,career_name,today,today,season_id,club_id,'ACTIVE')).lastrowid)
   if target_type=='selection':self.connection.execute('insert into manager_selection_assignments(manager_id,career_id,selection_id,status,appointed_at) values(?,?,?,?,?)',(mid,cid,target_id,'ACTIVE',today))
   self.connection.execute('insert into manager_history(manager_id,club_id,event_type,event_date,payload) values(?,?,?,?,?)',(mid,club_id,'CAREER_STARTED',today,f'{target_type}:{target_id}'))
  return {'manager_id':mid,'career_id':cid,'target_type':target_type,'target_id':target_id,'current_club_id':club_id}
 def sign(self,manager_id,club_id,start,end,salary,objective=None,bonus=0):
  c=self.connection.execute("select career_id from manager_careers where manager_id=? and status='ACTIVE'",(manager_id,)).fetchone()
  if not c:raise ValueError('NO_ACTIVE_CAREER')
  self.connection.execute("update manager_contracts set status='TERMINATED',end_date=? where manager_id=? and status='ACTIVE'",(start,manager_id));self.connection.execute('insert into manager_contracts(manager_id,club_id,start_date,end_date,salary,bonus,objective) values(?,?,?,?,?,?,?)',(manager_id,club_id,start,end,salary,bonus,objective));self.connection.execute('update managers set current_club_id=? where manager_id=?',(club_id,manager_id));self.connection.execute('update manager_careers set current_club_id=?,updated_at=? where career_id=?',(club_id,date.today().isoformat(),c[0]));self.connection.execute('insert into manager_history(manager_id,club_id,event_type,event_date,payload) values(?,?,?,?,?)',(manager_id,club_id,'CLUB_SIGNED',date.today().isoformat(),objective or ''));self.connection.commit()
 def objective(self,career_id,type_,priority=50,deadline=None):
  cur=self.connection.execute('insert into manager_objectives(career_id,type,priority,deadline) values(?,?,?,?)',(career_id,type_,priority,deadline));self.connection.commit();return int(cur.lastrowid)
 def inbox(self,manager_id,type_,title,body='',reference=None):
  self.connection.execute('insert or ignore into manager_inbox(manager_id,type,title,body,reference,created_at) values(?,?,?,?,?,?)',(manager_id,type_,title,body,reference,date.today().isoformat()));self.connection.commit()
 def resign(self,manager_id,reason='manager decision'):
  with self.connection:
   r=self.connection.execute('select current_club_id from managers where manager_id=?',(manager_id,)).fetchone();self.connection.execute("update managers set status='RESIGNED',active_career=0 where manager_id=?",(manager_id,));self.connection.execute("update manager_contracts set status='RESIGNED' where manager_id=? and status='ACTIVE'",(manager_id,));self.connection.execute('insert into manager_history(manager_id,club_id,event_type,event_date,payload) values(?,?,?,?,?)',(manager_id,r[0] if r else None,'RESIGNED',date.today().isoformat(),reason))
 def load(self,manager_id):return self.connection.execute('select * from managers where manager_id=?',(manager_id,)).fetchone()
 def close(self):self.connection.close()
