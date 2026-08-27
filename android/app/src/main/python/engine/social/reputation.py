from datetime import date
import sqlite3
from engine.core.state_store import assert_mutable_state_path

SCHEMA='''
CREATE TABLE IF NOT EXISTS competition_reputation(club_id INTEGER NOT NULL,competition_id INTEGER NOT NULL,season INTEGER NOT NULL,score REAL NOT NULL DEFAULT 50,PRIMARY KEY(club_id,competition_id,season));
CREATE TABLE IF NOT EXISTS reputation_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,competition_id INTEGER,season INTEGER NOT NULL,event_type TEXT NOT NULL,severity INTEGER NOT NULL,delta REAL NOT NULL,reference TEXT UNIQUE,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reputation_snapshots(snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,competition_id INTEGER,season INTEGER NOT NULL,month INTEGER NOT NULL,score REAL NOT NULL,created_at TEXT NOT NULL,UNIQUE(club_id,competition_id,season,month));
CREATE TABLE IF NOT EXISTS reputation_alerts(alert_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,competition_id INTEGER,season INTEGER NOT NULL,alert_type TEXT NOT NULL,message TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(club_id,competition_id,season,alert_type));
CREATE TABLE IF NOT EXISTS reputation_plans(plan_id INTEGER PRIMARY KEY AUTOINCREMENT,club_id INTEGER NOT NULL,goal REAL NOT NULL,deadline TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'PENDING',approved_by TEXT,approved_at TEXT);
'''
class ReputationService:
 def __init__(self,db):
  if not isinstance(db,sqlite3.Connection): assert_mutable_state_path(db)
  self.connection=sqlite3.connect(str(db)) if not isinstance(db,sqlite3.Connection) else db; self.connection.row_factory=sqlite3.Row; self.connection.executescript(SCHEMA); self.connection.commit()
 def preview_event(self,club_id,competition_id,season,event_type,severity,delta):
  if int(severity)<0 or float(delta)<-5 or float(delta)>5: raise ValueError('REPUTATION_EVENT_INVALID')
  row=self.connection.execute('SELECT score FROM competition_reputation WHERE club_id=? AND competition_id=? AND season=?',(club_id,competition_id,season)).fetchone(); score=float(row['score']) if row else 50.0
  return {'club_id':int(club_id),'competition_id':competition_id,'season':int(season),'current':score,'projected':max(0,min(100,score+float(delta))),'persisted':False}
 def record_event(self,club_id,competition_id,season,event_type,severity,delta,reference):
  preview=self.preview_event(club_id,competition_id,season,event_type,severity,delta)
  with self.connection:
   self.connection.execute('INSERT OR IGNORE INTO reputation_events(club_id,competition_id,season,event_type,severity,delta,reference,created_at) VALUES(?,?,?,?,?,?,?,?)',(club_id,competition_id,season,event_type,severity,delta,reference,date.today().isoformat()))
   self.connection.execute('INSERT INTO competition_reputation(club_id,competition_id,season,score) VALUES(?,?,?,?) ON CONFLICT(club_id,competition_id,season) DO UPDATE SET score=max(0,min(100,score+excluded.score-50))',(club_id,competition_id,season,preview['projected']))
  return {'reference':reference,'projected':preview['projected'],'persisted':True}
 def snapshot(self,club_id,competition_id,season,month):
  row=self.connection.execute('SELECT score FROM competition_reputation WHERE club_id=? AND competition_id=? AND season=?',(club_id,competition_id,season)).fetchone(); score=float(row['score']) if row else 50.0
  self.connection.execute('INSERT OR REPLACE INTO reputation_snapshots(club_id,competition_id,season,month,score,created_at) VALUES(?,?,?,?,?,?)',(club_id,competition_id,season,month,score,date.today().isoformat())); self.connection.commit(); return score
 def alerts(self,club_id,season):
  row=self.connection.execute('SELECT AVG(score) score FROM competition_reputation WHERE club_id=? AND season=?',(club_id,season)).fetchone(); score=float(row['score'] or 50)
  if score < 30: self.connection.execute('INSERT OR IGNORE INTO reputation_alerts(club_id,season,alert_type,message,created_at) VALUES(?,?,?,?,?)',(club_id,season,'CRITICAL','Reputação crítica',date.today().isoformat())); self.connection.commit()
  return [dict(r) for r in self.connection.execute('SELECT * FROM reputation_alerts WHERE club_id=? AND season=?',(club_id,season)).fetchall()]
 def comparison(self,club_id,season): return [dict(r) for r in self.connection.execute('SELECT * FROM reputation_snapshots WHERE club_id=? AND season=? ORDER BY month',(club_id,season)).fetchall()]
 def create_plan(self,club_id,goal,deadline):
  cur=self.connection.execute('INSERT INTO reputation_plans(club_id,goal,deadline) VALUES(?,?,?)',(club_id,goal,deadline)); self.connection.commit(); return int(cur.lastrowid)
 def approve_plan(self,plan_id,approved_by='manager'):
  with self.connection: self.connection.execute("UPDATE reputation_plans SET status='APPROVED',approved_by=?,approved_at=? WHERE plan_id=?",(approved_by,date.today().isoformat(),plan_id))
  return dict(self.connection.execute('SELECT * FROM reputation_plans WHERE plan_id=?',(plan_id,)).fetchone())
 def close(self): self.connection.close()
