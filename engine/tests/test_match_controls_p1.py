import sqlite3
from engine.competitions.match_engine import CompetitionService

def test_match_conditions_fatigue_discipline_and_event_review():
    service=CompetitionService(sqlite3.connect(':memory:'))
    season=service.create_season(2027)
    competition=service.create_competition('Liga',season,[1,2])
    match=service.generate_fixtures(competition)[0]
    assert service.configure_match_conditions(match,5,-3,'STRICT',True)['var_enabled'] == 1
    assert service.fatigue_by_minute(match,90)['home_fatigue'] > 0
    assert service.register_discipline(17,yellow=2)['yellow_cards'] == 2
    assert service.register_discipline(17,red=1)['suspension_matches'] == 1
    service.play(match,seed=7)
    event=service.match_events(match)[0]
    assert service.review_event(match,event['event_id'],'ANNUL','revisão VAR')['action'] == 'ANNUL'
    assert service.review_event(match,event['event_id'],'ANNUL','duplicada')['review_id'] == service.review_event(match,event['event_id'],'ANNUL','duplicada')['review_id']
    service.close()
