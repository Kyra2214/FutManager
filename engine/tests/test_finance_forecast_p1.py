import sqlite3
from datetime import date
from engine.world.time_and_finance import FinanceLedger, LogicalClock, WorldTickContext

def test_finance_recurring_budget_forecast_and_weekly_balance():
    c=sqlite3.connect(':memory:')
    LogicalClock(c)
    ledger=FinanceLedger(c)
    context=WorldTickContext('tick-1',date(2027,1,7),2027,1,1,'week')
    assert ledger.post(context,1,'INCOME','SPONSOR',1000,'contract','c1','receita') is True
    assert ledger.post(context,1,'EXPENSE','PAYROLL',-800,'payroll','p1','folha') is True
    assert ledger.add_recurring_rule(1,'PAYROLL',-500,'RULE','weekly-payroll','folha semanal')['amount']==-500
    assert ledger.apply_recurring(context,1)['applied']==1
    assert ledger.set_budget(1,2027,1,700)['limit_amount']==700
    assert ledger.weekly_balance(1,2027,1)['alert']['over_limit'] is True
    forecast=ledger.forecast(1,2027,1,4)
    assert forecast['recurring_weekly']==-500 and forecast['persisted'] is False
