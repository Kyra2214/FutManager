import sqlite3
from datetime import date
from engine.commercial.sponsorship_media import CommercialService
from engine.world.time_and_finance import LogicalClock

def test_sponsorship_preview_approval_audience_expiry_and_audit():
    service = CommercialService(sqlite3.connect(':memory:'))
    sponsor_id = service.sponsor('Marca A', 'varejo', 100000)
    preview = service.preview_contract(1, sponsor_id, 'MAIN', 5000, 500, 10, 'proposal-1')
    assert preview['persisted'] is False and preview['duplicate'] is False
    approved = service.approve_contract(1, sponsor_id, 'MAIN', 5000, 500, 10, '2026-01-01', '2026-10-01', 'proposal-1')
    again = service.approve_contract(1, sponsor_id, 'MAIN', 5000, 500, 10, '2026-01-01', '2026-10-01', 'proposal-1')
    assert approved['status'] == 'APPROVED' and again['contract_id'] == approved['contract_id']
    service.media_event(1, 'VICTORY', 10, 'media-1')
    assert service.audience(1)['exposure'] == 10
    assert service.contract_audit(1)['active_contracts'] == 1
    assert service.expire_contracts('2027-01-01') == 1
    service.close()
