import sqlite3
from engine.competitions.structure import CompetitionStructureService

def test_competition_formats_draw_tie_and_phase_prize():
    service=CompetitionStructureService(sqlite3.connect(':memory:'))
    config=service.configure_format(9,groups=4,legs=2,extra_time=True,away_goals=True,protected_draw=True)
    assert config['groups']==4 and config['legs']==2 and config['away_goals']==1
    assert service.draw_pots(9,2027,[[1,2],[3,4]],10)==service.draw_pots(9,2027,[[1,2],[3,4]],10)
    assert service.protected_draw([[1],[2]],10)==[(1,0),(2,1)]
    phase=service.add_phase(9,'KNOCKOUT',1,'KNOCKOUT')
    tie=service.create_tie(9,2027,phase,1,2)
    assert service.create_tie(9,2027,phase,1,2)==tie
    result=service.resolve_tie(tie,2,0,1,1)
    assert result['winner']==1 and result['aggregate']==[3,1]
    assert service.phase_prize(9,phase,1,100000)['amount']==100000
    service.close()
