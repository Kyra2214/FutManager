import sqlite3
import pytest
from engine.social.attendance import AttendanceService

def test_sector_ticketing_capacity_courtesy_refund_and_occupancy():
    service = AttendanceService(sqlite3.connect(':memory:'))
    sector = service.configure_sector(1, 'Norte', 10, 1.2)
    assert service.preview_sector_demand(50, 1)[0]['persisted'] is False
    sale = service.sell_tickets(50, 1, sector['sector_id'], 8, 40)
    assert sale['gross_revenue'] == 320
    with pytest.raises(ValueError, match='TICKET_CAPACITY_EXCEEDED'):
        service.sell_tickets(50, 1, sector['sector_id'], 3, 40)
    with pytest.raises(ValueError, match='COMPLIMENTARY_AUDIT_REQUIRED'):
        service.sell_tickets(50, 1, sector['sector_id'], 1, 40, complimentary=True)
    courtesy = service.sell_tickets(50, 1, sector['sector_id'], 1, 0, complimentary=True, reason='convidado', responsible='manager')
    assert courtesy['gross_revenue'] == 0
    assert service.occupancy(50, 1)['sold'] == 9
    refund = service.refund_ticket_sale(sale['sale_id'], 'cancelamento')
    assert refund['refund'] == 320
    with pytest.raises(KeyError):
        service.refund_ticket_sale(sale['sale_id'], 'duplicado')
