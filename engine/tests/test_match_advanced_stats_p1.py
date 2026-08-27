import sqlite3
from engine.competitions.match_engine import CompetitionService

def test_advanced_match_stats_preview_and_persistence():
    service=CompetitionService(sqlite3.connect(':memory:'))
    season=service.create_season(2027)
    competition=service.create_competition('Liga',season,[1,2])
    match=service.generate_fixtures(competition)[0]
    preview=service.advanced_preview(match,seed=10)
    assert preview['persisted'] is False
    result=service.play(match,seed=10)
    advanced=service.connection.execute('SELECT * FROM match_advanced_stats WHERE match_id=?',(match,)).fetchone()
    assert advanced is not None and advanced['home_duels'] >= 25
    assert service.advanced_preview(match)['persisted'] is False
    assert service.official_summary(match)['official'] is True
    service.close()
