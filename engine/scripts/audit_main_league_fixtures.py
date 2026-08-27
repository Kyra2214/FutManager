from pathlib import Path
import sqlite3
import json
DB=Path('/home/ubuntu/brasfoot_engine/data/state/game.db')
c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
result={}
tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
if 'career_parallel_fixtures' in tables:
 rows=c.execute("SELECT season_number, division, COUNT(*) AS total, COUNT(DISTINCT home_club_id) + COUNT(DISTINCT away_club_id) AS club_refs FROM career_parallel_fixtures GROUP BY season_number, division ORDER BY season_number, division").fetchall()
 result['parallel']=[dict(r) for r in rows]
 result['parallel_distinct_clubs']=[dict(r) for r in c.execute("SELECT season_number, division, COUNT(DISTINCT club_id) AS clubs FROM (SELECT season_number, division, home_club_id AS club_id FROM career_parallel_fixtures UNION ALL SELECT season_number, division, away_club_id AS club_id FROM career_parallel_fixtures) GROUP BY season_number, division ORDER BY season_number, division")]
 result['parallel_pair_duplicates']=[dict(r) for r in c.execute("SELECT season_number, division, home_club_id, away_club_id, COUNT(*) AS occurrences FROM career_parallel_fixtures GROUP BY season_number, division, home_club_id, away_club_id HAVING COUNT(*)>2 ORDER BY occurrences DESC LIMIT 10")]
 result['parallel_total_by_season']=[dict(r) for r in c.execute("SELECT season_number, COUNT(*) AS total FROM career_parallel_fixtures GROUP BY season_number ORDER BY season_number")]
 result['parallel_per_club_home_away']= [dict(r) for r in c.execute("SELECT season_number, home_club_id AS club_id, COUNT(*) AS matches FROM career_parallel_fixtures GROUP BY season_number, home_club_id ORDER BY season_number, club_id LIMIT 20")]
if 'career_parallel_entries' in tables:
 result['active_entries']=[dict(r) for r in c.execute("SELECT career_id, parallel_division, COUNT(*) AS rows, COUNT(DISTINCT club_id) AS distinct_clubs, COUNT(DISTINCT parallel_position) AS positions FROM career_parallel_entries WHERE status='ACTIVE' GROUP BY career_id, parallel_division ORDER BY career_id, parallel_division")]
for name in ('fixtures','competition_fixtures','matches'):
 if name in tables:
  cols={r[1] for r in c.execute(f'PRAGMA table_info({name})')}
  result[name]={'columns':sorted(cols),'count':c.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]}
print(json.dumps(result,ensure_ascii=False,indent=2))
c.close()
