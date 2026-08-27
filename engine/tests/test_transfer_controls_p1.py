import sqlite3
from datetime import date
from engine.transfers.market import TransferMarketService
from engine.world.time_and_finance import WorldTickContext, LogicalClock

def test_transfer_window_offer_counter_loan_and_audit():
    c=sqlite3.connect(':memory:')
    service=TransferMarketService(c)
    c.execute("INSERT INTO player_market_state(player_id,club_id,status,market_value,asking_price) VALUES(10,1,'ACTIVE',1000,1200)")
    window=service.open_window(2027,1,'2027-01-01','2027-03-01',{'international_registration_open':True})
    offer=service.create_offer(10,2,1,1000,window,1200,international=True)
    service.counter(offer,1100,2)
    service.approve_offer(offer,'manager')
    assert service.market_audit(2)['offers'][0]['manager_approved']==1
    c.execute("UPDATE player_market_state SET status='ACTIVE' WHERE player_id=10")
    loan=service.create_loan(10,1,2,'2027-02-01','2027-06-01',100,200,'2027-05-01')
    assert loan>0
    assert service.market_audit(2)['persisted'] is True
    service.close()
