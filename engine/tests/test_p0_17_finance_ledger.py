import sqlite3
from datetime import date

from engine.economy.world_economy import EconomyService
from engine.world.time_and_finance import FinanceLedger, WorldTickContext


def context():
    return WorldTickContext('p0-17:2026:2', date(2026, 1, 8), 2026, 2, 1, 'week', 17)


def test_ledger_has_single_currency_categories_and_idempotent_natural_reference(tmp_path):
    service = EconomyService(tmp_path / 'p0_17.db')
    service.ensure_club(1, cash=1000, budget=1000)
    first = service.ledger.post(context(), 1, 'INCOME', 'MATCHDAY', 250, 'match', 'm-1', 'Bilheteria')
    second = service.ledger.post(context(), 1, 'INCOME', 'MATCHDAY', 250, 'match', 'm-1', 'Bilheteria')
    assert FinanceLedger.CURRENCY == 'BRL'
    assert first is True and second is False
    assert service.ledger.close_week(context())['currency'] == 'BRL'
    service.close()


def test_projection_alert_reports_and_controlled_deficit(tmp_path):
    service = EconomyService(tmp_path / 'p0_17_reports.db')
    service.ensure_club(7, cash=1000, budget=1000)
    service.connection.execute('UPDATE club_economic_state SET payroll=300 WHERE club_id=7')
    service.ledger.post(context(), 7, 'INCOME', 'SPONSORSHIP', 500, 'sponsor', 's-1', 'Patrocínio')
    service.ledger.post(context(), 7, 'EXPENSE', 'PAYROLL', -200, 'payroll', 'p-1', 'Folha')
    service.connection.commit()
    assert service.projection_39_weeks(7, 100, 50)['weeks'] == 39
    assert service.low_balance_alert(7)['status'] == 'LOW_BALANCE'
    assert service.low_balance_alert(7)['persisted'] is True
    assert service.connection.execute("SELECT COUNT(*) FROM financial_alerts WHERE club_id=7 AND alert_type='LOW_BALANCE'").fetchone()[0] == 1
    assert service.report_revenue(7, 2026) == 500
    assert service.report_expense(7, 2026) == 200
    assert service.report_world(2026)['net'] == 300
    result = service.controlled_deficit(7, 90, context())
    assert result['posted'] is True and service.health(7).value in {'HEALTHY', 'STABLE', 'CRITICAL'}
    assert service.audit_season(2026)['world']['entries'] == 3
    assert service.audit_season(2026)['persisted'] is True
    assert service.connection.execute('SELECT COUNT(*) FROM economy_season_audits WHERE season=2026').fetchone()[0] == 1
    service.close()


def test_ledger_rejects_non_integer_amount_and_invalid_category(tmp_path):
    service = EconomyService(tmp_path / 'p0_17_validation.db')
    with __import__('pytest').raises(ValueError, match='LEDGER_CATEGORY_INVALID'):
        service.ledger.post(context(), 1, 'EXPENSE', 'UNKNOWN', -1, 'x', '1', 'x')
    with __import__('pytest').raises(ValueError, match='LEDGER_AMOUNT_MUST_BE_INTEGER'):
        service.ledger.post(context(), 1, 'EXPENSE', 'OTHER', -1.5, 'x', '2', 'x')
    service.close()
