from datetime import date
import sqlite3
from engine.core.state_store import assert_mutable_state_path

SCHEMA='''
CREATE TABLE IF NOT EXISTS board_members(member_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,name TEXT NOT NULL,role TEXT NOT NULL,mandate_start TEXT NOT NULL,mandate_end TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'ACTIVE');
CREATE TABLE IF NOT EXISTS board_decisions(decision_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,subject TEXT NOT NULL,required_quorum INTEGER NOT NULL,extraordinary INTEGER NOT NULL DEFAULT 0,status TEXT NOT NULL DEFAULT 'PENDING',justification TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS board_votes(vote_id INTEGER PRIMARY KEY AUTOINCREMENT,decision_id INTEGER NOT NULL,member_id INTEGER NOT NULL,vote TEXT NOT NULL,conflict INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,UNIQUE(decision_id,member_id));
CREATE TABLE IF NOT EXISTS board_minutes(minutes_id INTEGER PRIMARY KEY AUTOINCREMENT,decision_id INTEGER NOT NULL,body TEXT NOT NULL,created_at TEXT NOT NULL);
'''
class BoardService:
 def __init__(self,db):
  if not isinstance(db,sqlite3.Connection): assert_mutable_state_path(db)
  self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db; self.connection.row_factory=sqlite3.Row; self.connection.executescript(SCHEMA); self.connection.commit()
 def add_member(self,club_id,name,role,mandate_start,mandate_end):
  cur=self.connection.execute('INSERT INTO board_members(club_id,name,role,mandate_start,mandate_end) VALUES(?,?,?,?,?)',(club_id,name,role,mandate_start,mandate_end)); self.connection.commit(); return int(cur.lastrowid)
 def create_decision(self,club_id,subject,required_quorum=1,extraordinary=False,justification=''):
  if int(required_quorum)<1: raise ValueError('QUORUM_INVALID')
  cur=self.connection.execute('INSERT INTO board_decisions(club_id,subject,required_quorum,extraordinary,justification,created_at) VALUES(?,?,?,?,?,?)',(club_id,subject,required_quorum,int(bool(extraordinary)),justification,date.today().isoformat())); self.connection.commit(); return int(cur.lastrowid)
 def vote(self,decision_id,member_id,vote,conflict=False):
  decision=self.connection.execute('SELECT * FROM board_decisions WHERE decision_id=?',(decision_id,)).fetchone(); member=self.connection.execute('SELECT * FROM board_members WHERE member_id=?',(member_id,)).fetchone()
  if not decision or not member or member['club_id']!=decision['club_id']: raise ValueError('BOARD_SCOPE_INVALID')
  if conflict: return {'accepted':False,'reason':'CONFLICT_OF_INTEREST'}
  if vote not in ('YES','NO','ABSTAIN'): raise ValueError('VOTE_INVALID')
  with self.connection: self.connection.execute('INSERT OR REPLACE INTO board_votes(decision_id,member_id,vote,conflict,created_at) VALUES(?,?,?,?,?)',(decision_id,member_id,vote,0,date.today().isoformat()))
  return {'accepted':True,'decision_id':decision_id,'member_id':member_id,'vote':vote}
 def resolve(self,decision_id):
  decision=self.connection.execute('SELECT * FROM board_decisions WHERE decision_id=?',(decision_id,)).fetchone()
  if not decision: raise KeyError(decision_id)
  votes=self.connection.execute("SELECT * FROM board_votes WHERE decision_id=? AND conflict=0 AND vote!='ABSTAIN'",(decision_id,)).fetchall(); yes=sum(v['vote']=='YES' for v in votes); no=sum(v['vote']=='NO' for v in votes)
  status='APPROVED' if len(votes)>=decision['required_quorum'] and yes>no else 'REJECTED' if len(votes)>=decision['required_quorum'] else 'PENDING'
  self.connection.execute('UPDATE board_decisions SET status=? WHERE decision_id=?',(status,decision_id)); self.connection.commit(); return {'decision_id':int(decision_id),'status':status,'quorum':int(decision['required_quorum']),'votes':len(votes),'yes':yes,'no':no}
 def minutes(self,decision_id,body):
  cur=self.connection.execute('INSERT INTO board_minutes(decision_id,body,created_at) VALUES(?,?,?)',(decision_id,body,date.today().isoformat())); self.connection.commit(); return int(cur.lastrowid)
 def pending(self,club_id): return [dict(r) for r in self.connection.execute("SELECT * FROM board_decisions WHERE club_id=? AND status='PENDING' ORDER BY decision_id",(club_id,)).fetchall()]
 def history(self,club_id): return [dict(r) for r in self.connection.execute('SELECT * FROM board_decisions WHERE club_id=? ORDER BY decision_id',(club_id,)).fetchall()]
 def close(self): self.connection.close()
