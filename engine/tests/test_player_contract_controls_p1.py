import sqlite3
from engine.players.contracts import PlayerContractService

def test_contract_preview_termination_history_and_audit():
    connection=sqlite3.connect(':memory:')
    connection.execute('CREATE TABLE player_contract_history(contract_id INTEGER PRIMARY KEY AUTOINCREMENT,player_id INTEGER,club_id INTEGER,start_season INTEGER,start_week INTEGER,end_season INTEGER,end_week INTEGER,weekly_salary INTEGER,release_clause INTEGER,status TEXT,source TEXT)')
    connection.execute("INSERT INTO player_contract_history(player_id,club_id,start_season,start_week,end_season,end_week,weekly_salary,status,source) VALUES(10,1,2027,1,2028,52,1000,'ACTIVE','seed')")
    service=PlayerContractService(connection)
    preview=service.preview_renewal(10,1,1200,52,500,1000)
    assert preview['persisted'] is False and preview['current_salary']==1000
    terminated=service.terminate_early(1,2027,12,'ajuste de elenco')
    assert terminated['status']=='TERMINATED'
    assert service.terminate_early(1,2027,12,'ajuste duplicado')['status']=='TERMINATED'
    assert len(service.salary_history(10,1))==1
    assert service.contract_audit(10,1)['events'][0]['event_type']=='TERMINATION'
    service.close()
