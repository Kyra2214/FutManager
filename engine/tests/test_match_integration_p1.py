import sqlite3
from engine.competitions.match_engine import CompetitionService

def test_match_official_report_recovery_audit_and_idempotent_reprocess():
    service=CompetitionService(sqlite3.connect(':memory:'))
    season=service.create_season(2027)
    competition=service.create_competition('Liga',season,[1,2])
    match=service.generate_fixtures(competition)[0]
    service.play(match,seed=22)
    report=service.post_match_report(match,3,'recuperação padrão')
    assert report['recovery_days']==3
    audit=service.result_audit(match)
    assert audit['persisted'] is True and audit['advanced'] is not None
    first=service.reprocess_result(match,'auditoria VAR',seed=22)
    second=service.reprocess_result(match,'auditoria VAR',seed=22)
    assert first['status']=='REPROCESS_REQUESTED' and second['status']=='ALREADY_REQUESTED'
    service.close()
