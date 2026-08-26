import sqlite3
from engine.events.service import ClubEventService

def test_notification_preferences_snooze_group_bulk_read_and_failure():
    service = ClubEventService(sqlite3.connect(':memory:'))
    service.record(1,'COMPETICAO','NORMAL','Jogo','Aviso','fixture:1',origin='fixture')
    service.record(1,'FINANCEIRO','HIGH','Caixa','Falha','finance:1',origin='ledger')
    assert service.set_preference(1,'FINANCEIRO',False)['enabled'] is False
    assert service.snooze(1,2,'2026-02-01') is True
    assert service.group_notifications(1)[0]['count'] >= 1
    assert service.mark_all_read(1) == 2
    assert service.record_operational_failure(1,'DB_TIMEOUT','gateway','tempo excedido','failure:1') is True
    assert service.mark_all_read(1) == 1
