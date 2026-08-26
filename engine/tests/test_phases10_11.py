from pathlib import Path
import sqlite3,sys,tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from engine.competitions.match_engine import CompetitionService
from engine.competitions.structure import CompetitionStructureService
BASE=ROOT/'data/database/game.db'
def clone(p):
 a=sqlite3.connect(BASE);b=sqlite3.connect(p);a.backup(b);a.close();b.close()

def test_phases_rounds_fixtures_calendar_and_finish():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'s.db';clone(p); c=CompetitionService(p); s=CompetitionStructureService(p); season=c.create_season(2026); comp=c.create_competition('Liga',season,[1,2]); phase=s.add_phase(comp); ids=s.generate_fixtures(comp,phase,season,[1,2]); assert len(ids)==1; assert len(s.calendar(comp,1))==1
  try:s.finish_competition(comp)
  except ValueError as e:assert str(e)=='PENDING_FIXTURES'
  else:raise AssertionError('competição encerrada com fixture pendente')
  c.play(c.generate_fixtures(comp)[0],70,60,seed=2); s.connection.execute("update fixtures set status='PLAYED' where competition_id=?",(comp,)); s.connection.commit(); assert s.finish_competition(comp) is True; assert s.finish_competition(comp) is False; c.close();s.close()

def test_configurable_points_and_scorer_query():
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'s.db';clone(p); c=CompetitionService(p); season=c.create_season(2026); comp=c.create_competition('Liga',season,[1,2]); ids=c.generate_fixtures(comp); c.play(ids[0],60,60,seed=1); assert sum(x['points'] for x in c.standings(comp)) in (2,3); c.close()
