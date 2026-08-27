import sqlite3
from datetime import date
from engine.transfers.market import TransferMarketService
from engine.world.time_and_finance import WorldTickContext


def make_db(tmp_path):
    path=tmp_path/'transfer.db'; con=sqlite3.connect(path)
    con.executescript('''
      CREATE TABLE club_finances(club_id INTEGER PRIMARY KEY,cash INTEGER NOT NULL,updated_at TEXT NOT NULL);
      INSERT INTO club_finances VALUES(1,1000000,'2026-01-01'); INSERT INTO club_finances VALUES(2,1000000,'2026-01-01');
      CREATE TABLE player_market_state(player_id INTEGER PRIMARY KEY,club_id INTEGER,status TEXT,market_value INTEGER,asking_price INTEGER,release_clause INTEGER);
      INSERT INTO player_market_state VALUES(77,2,'ACTIVE',300000,400000,NULL);
    '''); con.commit(); con.close(); return path


def test_transfer_approval_costs_and_loan(tmp_path):
    market=TransferMarketService(make_db(tmp_path)); window=market.open_window(2026,1,'2026-01-01','2026-02-01')
    assert len(market.transferable_players(2)) == 1
    offer=market.create_offer(77,1,2,300000,window,400000,salary=10000,commission=20000,accessory_cost=5000)
    market.accept(offer)
    context=WorldTickContext('transfer-1',date(2026,1,8),2026,1,1,'week',1)
    market.complete(offer,context)
    assert market.connection.execute('select cash from club_finances where club_id=1').fetchone()[0] == 675000
    market.connection.execute("update player_market_state set club_id=1,status='ACTIVE' where player_id=77"); market.connection.commit()
    loan=market.create_loan(77,1,2,'2026-02-01','2026-06-01',1000,50000,'2026-05-01')
    assert loan > 0
    market.close()


def test_transfer_requires_approval_when_accepted_without_manager(tmp_path):
    market=TransferMarketService(make_db(tmp_path)); window=market.open_window(2026,1,'2026-01-01','2026-02-01')
    offer=market.create_offer(77,1,2,100000,window)
    market.connection.execute("update transfer_offers set status='ACCEPTED' where offer_id=?",(offer,)); market.connection.commit()
    try:
        market.complete(offer,WorldTickContext('transfer-2',date(2026,1,8),2026,1,1,'week',2))
    except ValueError as error:
        assert str(error)=='MANAGER_APPROVAL_REQUIRED'
    else: raise AssertionError('oferta aceita sem aprovação foi concluída')
    market.close()


def test_transfer_guards_suspension_and_roster_capacity(tmp_path):
    path=make_db(tmp_path); con=sqlite3.connect(path)
    con.execute('CREATE TABLE player_sport_state(player_id INTEGER,club_id INTEGER,available INTEGER,recovery_days INTEGER)')
    con.executemany('INSERT INTO player_sport_state VALUES(?,?,?,?)', [(i,1,1,0) for i in range(1,41)])
    con.execute('CREATE TABLE player_suspensions(player_id INTEGER,active INTEGER,until_date TEXT)')
    con.execute("INSERT INTO player_suspensions VALUES(77,1,'2099-01-01')"); con.commit(); con.close()
    market=TransferMarketService(path); window=market.open_window(2026,1,'2026-01-01','2026-02-01')
    try: market.create_offer(77,1,2,100000,window)
    except ValueError as error: assert str(error)=='ROSTER_CAPACITY_REACHED'
    else: raise AssertionError('limite de elenco não aplicado')
    con=market.connection; con.execute('DELETE FROM player_sport_state WHERE club_id=1'); con.commit()
    try: market.create_offer(77,1,2,100000,window)
    except ValueError as error: assert str(error)=='TRANSFER_BLOCKED_SUSPENDED'
    else: raise AssertionError('suspensão não bloqueou transferência')
    market.close()


def test_transfer_history_expiration_and_budget_filter(tmp_path):
    market = TransferMarketService(make_db(tmp_path))
    window = market.open_window(2026, 1, '2026-01-01', '2026-02-01')
    offer = market.create_offer(77, 1, 2, 300000, window, valid_until='2026-01-10')
    market.counter(offer, 320000)
    assert len(market.negotiation_history(offer)) == 2
    assert market.expire_offers('2026-01-11') == 1
    assert market.expire_offers('2026-01-11') == 0
    assert market.negotiation_alerts(1)[0]['status'] == 'EXPIRED'
    assert len(market.transferable_players(2, max_budget=500000)) == 0
    market.close()


def test_transfer_completion_is_single_winner(tmp_path):
    market = TransferMarketService(make_db(tmp_path))
    window = market.open_window(2026, 1, '2026-01-01', '2026-02-01')
    offer = market.create_offer(77, 1, 2, 100000, window)
    market.accept(offer)
    context = WorldTickContext('transfer-concurrency', date(2026, 1, 8), 2026, 1, 1, 'week', 3)
    market.complete(offer, context)
    try:
        market.complete(offer, context)
    except ValueError as error:
        assert str(error) == 'ALREADY_COMPLETED'
    else:
        raise AssertionError('a mesma oferta foi concluída duas vezes')
    market.close()
