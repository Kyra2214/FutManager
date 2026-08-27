from __future__ import annotations
from datetime import date
import sqlite3
from engine.world.time_and_finance import FinanceLedger,WorldTickContext,LogicalClock
from engine.core.state_store import assert_mutable_state_path
SCHEMA='''
CREATE TABLE IF NOT EXISTS sponsors(sponsor_id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE,sector TEXT,reputation INTEGER NOT NULL DEFAULT 50,budget INTEGER NOT NULL DEFAULT 0,market TEXT,preference TEXT,status TEXT NOT NULL DEFAULT 'ACTIVE');
CREATE TABLE IF NOT EXISTS sponsorship_contracts(contract_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,sponsor_id INTEGER NOT NULL,type TEXT NOT NULL,total_value INTEGER NOT NULL,periodic_value INTEGER NOT NULL,duration INTEGER NOT NULL,start_date TEXT NOT NULL,end_date TEXT NOT NULL,bonus INTEGER NOT NULL DEFAULT 0,goals TEXT NOT NULL DEFAULT '{}',status TEXT NOT NULL DEFAULT 'ACTIVE');
CREATE TABLE IF NOT EXISTS sponsorship_objectives(objective_id INTEGER PRIMARY KEY AUTOINCREMENT,contract_id INTEGER NOT NULL,type TEXT NOT NULL,target REAL NOT NULL,bonus INTEGER NOT NULL,achieved INTEGER NOT NULL DEFAULT 0,pay_reference TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS media_profiles(club_id INTEGER PRIMARY KEY,exposure INTEGER NOT NULL DEFAULT 0,interest INTEGER NOT NULL DEFAULT 0,reach INTEGER NOT NULL DEFAULT 0,trending INTEGER NOT NULL DEFAULT 0,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS media_events(media_event_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,type TEXT NOT NULL,exposure_delta INTEGER NOT NULL,event_date TEXT NOT NULL,reference TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS media_rights_contracts(rights_id INTEGER PRIMARY KEY AUTOINCREMENT,competition_id INTEGER NOT NULL,season_id INTEGER NOT NULL,value INTEGER NOT NULL,periodicity TEXT NOT NULL,start_date TEXT NOT NULL,end_date TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'ACTIVE');
CREATE TABLE IF NOT EXISTS sponsorship_proposals(proposal_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,sponsor_id INTEGER NOT NULL,type TEXT NOT NULL,total_value INTEGER NOT NULL,periodic_value INTEGER NOT NULL,duration INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'PENDING',reference TEXT UNIQUE,created_at TEXT NOT NULL);
'''
class CommercialService:
 def __init__(self,db):
  assert_mutable_state_path(db) if not isinstance(db,sqlite3.Connection) else None;self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db;self.connection.row_factory=sqlite3.Row;self.connection.execute('PRAGMA foreign_keys=ON');self.connection.executescript(SCHEMA);self.connection.commit();LogicalClock(self.connection);self.ledger=FinanceLedger(self.connection)
 def sponsor(self,name,sector='',budget=0,market='',preference=''):
  cur=self.connection.execute('insert into sponsors(name,sector,budget,market,preference) values(?,?,?,?,?)',(name,sector,budget,market,preference));self.connection.commit();return int(cur.lastrowid)
 def preview_contract(self,club_id,sponsor_id,type_,total,periodic,duration,reference):
  if int(total) < 0 or int(periodic) < 0 or int(duration) < 1 or not str(reference).strip(): raise ValueError('SPONSOR_CONTRACT_INVALID')
  duplicate=self.connection.execute('SELECT proposal_id FROM sponsorship_proposals WHERE reference=?',(str(reference).strip(),)).fetchone()
  sponsor=self.connection.execute('SELECT reputation,budget FROM sponsors WHERE sponsor_id=?',(int(sponsor_id),)).fetchone()
  if sponsor is None: raise KeyError(sponsor_id)
  return {'club_id':int(club_id),'sponsor_id':int(sponsor_id),'total_value':int(total),'periodic_value':int(periodic),'duration':int(duration),'reputation':int(sponsor['reputation']),'budget':int(sponsor['budget']),'duplicate':duplicate is not None,'persisted':False}

 def approve_contract(self,club_id,sponsor_id,type_,total,periodic,duration,start,end,reference,bonus=0,goals='{}'):
  preview=self.preview_contract(club_id,sponsor_id,type_,total,periodic,duration,reference)
  with self.connection:
   self.connection.execute('INSERT OR IGNORE INTO sponsorship_proposals(club_id,sponsor_id,type,total_value,periodic_value,duration,status,reference,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(club_id,sponsor_id,type_,total,periodic,duration,'APPROVED',str(reference).strip(),date.today().isoformat()))
   proposal=self.connection.execute('SELECT proposal_id FROM sponsorship_proposals WHERE reference=?',(str(reference).strip(),)).fetchone()
   self.connection.execute('INSERT OR IGNORE INTO sponsorship_contracts(contract_id,club_id,sponsor_id,type,total_value,periodic_value,duration,start_date,end_date,bonus,goals,status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(proposal['proposal_id'],club_id,sponsor_id,type_,total,periodic,duration,start,end,bonus,goals,'ACTIVE'))
  return {'proposal_id':int(proposal['proposal_id']),'contract_id':int(proposal['proposal_id']),'status':'APPROVED','preview':preview}

 def contract_audit(self,club_id):
  contracts=[dict(row) for row in self.connection.execute('SELECT * FROM sponsorship_contracts WHERE club_id=? ORDER BY contract_id',(int(club_id),)).fetchall()]
  objectives=[dict(row) for row in self.connection.execute('SELECT o.* FROM sponsorship_objectives o JOIN sponsorship_contracts c ON c.contract_id=o.contract_id WHERE c.club_id=? ORDER BY o.objective_id',(int(club_id),)).fetchall()]
  return {'club_id':int(club_id),'contracts':contracts,'objectives':objectives,'active_contracts':sum(row['status']=='ACTIVE' for row in contracts)}

 def contract(self,club_id,sponsor_id,type_,total,periodic,duration,start,end,bonus=0,goals='{}'):
  cur=self.connection.execute('insert into sponsorship_contracts(club_id,sponsor_id,type,total_value,periodic_value,duration,start_date,end_date,bonus,goals) values(?,?,?,?,?,?,?,?,?,?)',(club_id,sponsor_id,type_,total,periodic,duration,start,end,bonus,goals));self.connection.commit();return int(cur.lastrowid)
 def objective(self,contract_id,type_,target,bonus):
  cur=self.connection.execute('insert into sponsorship_objectives(contract_id,type,target,bonus,pay_reference) values(?,?,?,?,?)',(contract_id,type_,target,bonus,f'objective:{contract_id}:{type_}'));self.connection.commit();return int(cur.lastrowid)
 def pay_objective(self,objective_id,context:WorldTickContext,achieved=True):
  with self.connection:
   o=self.connection.execute('select * from sponsorship_objectives where objective_id=?',(objective_id,)).fetchone()
   if not o:raise KeyError(objective_id)
   if o['achieved'] or not achieved:return False
   c=self.connection.execute('select club_id from sponsorship_contracts where contract_id=?',(o['contract_id'],)).fetchone();self.ledger.post(context,c[0],'INCOME','SPONSOR',o['bonus'],'sponsorship_objective',o['pay_reference'],'Bônus de patrocínio');self.connection.execute('update sponsorship_objectives set achieved=1 where objective_id=?',(objective_id,));return True
 def media_event(self,club_id,type_,delta,reference):
  with self.connection:
   cur=self.connection.execute('insert or ignore into media_events(club_id,type,exposure_delta,event_date,reference) values(?,?,?,?,?)',(club_id,type_,delta,date.today().isoformat(),reference));
   if cur.rowcount:
    self.connection.execute('insert or ignore into media_profiles(club_id,updated_at) values(?,?)',(club_id,date.today().isoformat()));self.connection.execute('update media_profiles set exposure=max(0,min(100,exposure+?)),interest=max(0,min(100,interest+?)),reach=max(0,reach+?),trending=?,updated_at=? where club_id=?',(delta,delta//2,delta*10,delta,date.today().isoformat(),club_id))
 def audience(self,club_id):
  row=self.connection.execute('SELECT * FROM media_profiles WHERE club_id=?',(int(club_id),)).fetchone()
  return dict(row) if row else {'club_id':int(club_id),'exposure':0,'interest':0,'reach':0,'trending':0}

 def media_revenue(self,club_id,value,context,reference):
  self.ledger.post(context,club_id,'INCOME','MEDIA',value,'media',reference,'Receita de mídia');return value
 def expire_contracts(self,as_of):
  cur=self.connection.execute("update sponsorship_contracts set status='EXPIRED' where status='ACTIVE' and end_date<?",(as_of,));self.connection.commit();return cur.rowcount
 def close(self):self.connection.close()
