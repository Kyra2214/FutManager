import shutil
import sqlite3
import tempfile
from pathlib import Path

from engine.manager.career import ManagerService

source = Path(__file__).resolve().parents[1] / 'data/state/game.db'
with tempfile.TemporaryDirectory() as folder:
    target = Path(folder) / 'game.db'
    shutil.copyfile(source, target)
    before = sqlite3.connect(target).execute('select count(*) from times').fetchone()[0]
    service = ManagerService(str(target))
    result = service.start_career('Smoke Parallel', 'BR', 30, 'Universo 4 países', 'club', 2009, selected_country_ids=[29, 104, 65, 154])
    after = service.connection.execute('select count(*) from times').fetchone()[0]
    league = service.connection.execute('select total_clubs, source_country_count, division_count from career_parallel_leagues where career_id=?', (result['career_id'],)).fetchone()
    divisions = service.connection.execute('select parallel_division,count(*) from career_parallel_entries where career_id=? group by parallel_division order by parallel_division', (result['career_id'],)).fetchall()
    target_division = service.connection.execute('select parallel_division from career_parallel_entries where career_id=? and club_id=2009', (result['career_id'],)).fetchone()[0]
    assert before == after
    assert tuple(league) == (78, 4, 4), league
    assert sum(row[1] for row in divisions) == 78
    assert target_division == 4
    print({'result': result['parallel_league'], 'divisions': [tuple(row) for row in divisions], 'target_division': target_division, 'times_unchanged': before == after})
