import sqlite3
from engine.players.contracts import PlayerContractService

def test_player_registration_roles_clause_and_bonuses():
    service=PlayerContractService(sqlite3.connect(':memory:'))
    registered=service.register_player(10,1,2027,foreign_player=True,shirt_number=9)
    assert registered['registration_status']=='REGISTERED' and registered['foreign_player']==1
    assert service.set_squad_role(10,1,2027,'CAPTAIN',1200)['minutes_promise']==1200
    clause=service.set_release_clause(10,1,55,1000000)
    assert clause['amount']==1000000
    bonus=service.add_contract_bonus(10,1,55,'GOALS',5000,10)
    assert service.progress_bonus(bonus['bonus_id'],10)['status']=='ACHIEVED'
    try:
        service.register_player(11,1,2027,shirt_number=9)
    except ValueError as error:
        assert str(error)=='SHIRT_NUMBER_UNAVAILABLE'
    else:
        raise AssertionError('duplicate shirt number accepted')
    service.close()
