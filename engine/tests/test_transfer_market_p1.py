import sqlite3
from engine.transfers.market import TransferMarketService

def test_market_valuation_and_shortlist_are_persisted():
    service = TransferMarketService(sqlite3.connect(':memory:'))
    service.connection.execute("INSERT INTO player_market_state(player_id,club_id,status,market_value,asking_price) VALUES(?,?,?,?,?)", (7, 10, 'ACTIVE', 0, 0))
    service.connection.commit()
    preview = service.evaluate_player(7, strength=70, potential=80)
    assert preview['persisted'] is False and preview['market_value'] == 110000
    row = service.shortlist(1, 7, priority=5, notes='titular')
    assert row['status'] == 'ACTIVE'
    service.shortlist(1, 7, priority=8, notes='prioridade alta')
    audit = service.shortlist_audit(1)
    assert audit['count'] == 1 and audit['players'][0]['priority'] == 8
    service.close()
