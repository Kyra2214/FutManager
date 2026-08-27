import sqlite3
from engine.economy.staff_market import StaffMarketService

def test_staff_levels_vacancies_org_bonus_and_audit():
    connection=sqlite3.connect(':memory:')
    connection.execute('CREATE TABLE times(time_id INTEGER PRIMARY KEY)')
    connection.execute('INSERT INTO times(time_id) VALUES(1)')
    service=StaffMarketService(connection)
    assert service.seed_catalog() == 10
    staff_id=service.connection.execute('SELECT staff_id FROM staff_members ORDER BY staff_id LIMIT 1').fetchone()[0]
    org=service.set_organization_role(staff_id,1,'COMISSAO',rank=3,leadership=True)
    assert org['leadership']==1
    bonus=service.add_performance_bonus(staff_id,1,'TITLE',10000,1)
    assert bonus['threshold']==1
    vacancies=service.staff_vacancies(1,required_roles=['treinador','medico'])
    assert 'treinador' in vacancies
    audit=service.contract_audit(1)
    assert audit['persisted'] is True and audit['organization'][0]['staff_id']==staff_id
    service.close()
