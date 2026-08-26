import sqlite3
import pytest
from engine.commercial.licensing_inventory import LicensingInventoryService

def test_licensing_inventory_sales_refunds_alerts_and_segments():
    service = LicensingInventoryService(sqlite3.connect(':memory:'))
    preview = service.preview_contract(1, 'Partner', 1000, 100, '2026-01-01', '2026-12-31', 'lic-1')
    assert preview['persisted'] is False
    approved = service.approve_contract(1, 'Partner', 1000, 100, '2026-01-01', '2026-12-31', 'lic-1')
    assert approved['status'] == 'APPROVED'
    product = service.add_product(1, 'Camisa', 'local', 50, low_stock_threshold=2)
    lot = service.add_lot(product['product_id'], 5)
    sale = service.sell_lot(1, product['product_id'], 3, 'local', 'sale-1')
    assert sale['revenue'] == 150
    with pytest.raises(ValueError, match='STOCK_UNAVAILABLE'):
        service.sell_lot(1, product['product_id'], 3, 'local', 'sale-2')
    assert service.stock_alerts(1)[0]['low'] is True
    assert service.sales_by_segment(1)[0]['revenue'] == 150
    assert service.refund_sale(sale['sale_id'], 'devolução')['refund'] == 150
    with pytest.raises(KeyError): service.refund_sale(sale['sale_id'], 'duplicado')
    service.close()
