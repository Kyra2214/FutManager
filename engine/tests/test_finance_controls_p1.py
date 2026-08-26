from datetime import date
import sqlite3
from engine.world.time_and_finance import FinanceLedger, LogicalClock

def test_finance_preview_reconciliation_and_budget_alert():
    con = sqlite3.connect(':memory:')
    clock = LogicalClock(con, start_date=date(2026, 1, 1), season=2026)
    ledger = FinanceLedger(con)
    context = clock.next_week_context(seed=1)
    assert ledger.preview_post(context, 1, 'EXPENSE', 'SALARY', -100, 'staff', 's-1', 'folha')['persisted'] is False
    assert ledger.post(context, 1, 'EXPENSE', 'SALARY', -100, 'staff', 's-1', 'folha') is True
    assert ledger.preview_post(context, 1, 'EXPENSE', 'SALARY', -100, 'staff', 's-1', 'folha')['duplicate'] is True
    assert ledger.reconcile_club(1, context.season)['reconciled'] is True
    assert ledger.budget_alert(1, context.season, context.week, 50)['over_limit'] is True
