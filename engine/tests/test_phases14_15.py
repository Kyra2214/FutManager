from pathlib import Path
import sqlite3,sys,tempfile
from datetime import date
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.social.stadium_fans import SocialService
from engine.commercial.sponsorship_media import CommercialService
from engine.world.time_and_finance import WorldTickContext
BASE=ROOT/'data/database/game.db'
def clone(p):
 a=sqlite3.connect(BASE);b=sqlite3.connect(p);a.backup(b);a.close();b.close()

def test_stadium_fans_attendance_revenue_and_reputation():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'s.db';clone(p);s=SocialService(p);s.ensure_fan_reputation(1,10000);sid=s.create_stadium(1,'Arena',20000,cost=100);ctx=WorldTickContext('s1',date(2026,1,1),2026,1,1);s.upgrade(sid,'comfort',5,100,ctx);a=s.attendance(100,1,ctx,visitor_reputation=60,importance=80,ticket_price=20,seed=4);assert 0<=a.actual<=20000;assert s.attendance(100,1,ctx).actual==a.actual;s.record_matchday_revenue(100,ctx);s.update_reputation(1,5,2);s.event(1,'SPORTING','Vitória','resultado',reference='match:100');assert s.connection.execute('select count(*) from club_events').fetchone()[0]==1;s.close()

def test_sponsor_bonus_media_and_expiration():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'s.db';clone(p);s=CommercialService(p);sid=s.sponsor('Marca Fictícia','varejo',100000);cid=s.contract(1,sid,'MAIN',100000,10000,12,'2026-01-01','2027-01-01',bonus=5000);oid=s.objective(cid,'WINS',10,5000);ctx=WorldTickContext('c1',date(2026,6,1),2026,22,6);assert s.pay_objective(oid,ctx);assert not s.pay_objective(oid,ctx);s.media_event(1,'BIG_WIN',10,'match:1');s.media_event(1,'BIG_WIN',10,'match:1');assert s.connection.execute('select exposure from media_profiles where club_id=1').fetchone()[0]==10;s.media_revenue(1,1000,ctx,'media:1');assert s.expire_contracts('2028-01-01')==1;s.close()
