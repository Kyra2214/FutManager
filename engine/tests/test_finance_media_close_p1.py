import sqlite3
from datetime import date
from engine.world.time_and_finance import FinanceLedger, LogicalClock, WorldTickContext

def test_media_reconciliation_and_monthly_close():
    c=sqlite3.connect(':memory:'); LogicalClock(c); ledger=FinanceLedger(c)
    context=WorldTickContext('media-1',date(2027,1,15),2027,2,1,'week')
    for category,amount,source in [('MEDIA',1000,'tv'),('MATCHDAY_REVENUE',500,'gate'),('SPONSOR_PAYMENT',800,'sponsor'),('PRIZE',200,'cup'),('TAX',-100,'tax'),('TRAVEL',-150,'travel')]:
        assert ledger.post(context,1,'INCOME' if amount>0 else 'EXPENSE',category,amount,source,source,category)
    summary=ledger.media_revenue_summary(1,2027)
    assert summary['net']==2250 and summary['persisted'] is True
    recon=ledger.cross_domain_reconciliation(1,2027)
    assert recon['reconciled'] is True
    close=ledger.monthly_close(1,2027,1)
    assert close['closed'] is True and close['net']==2250
