import sqlite3
import pytest
from engine.core.gateway_contracts import GatewayContractService

def test_gateway_contracts_validation_idempotency_and_scope():
    service = GatewayContractService(sqlite3.connect(':memory:'))
    assert len(service.catalog()) >= 5
    assert service.validate('finance_summary', {})['mutating'] is False
    with pytest.raises(ValueError, match='GATEWAY_REQUIRED:amount'):
        service.validate('finance_revenue', {'reference':'r1'})
    with pytest.raises(ValueError, match='GATEWAY_READ_ONLY'):
        service.audit_mutation('finance_summary', {}, 'read-1')
    first = service.audit_mutation('finance_revenue', {'amount':100,'reference':'r1'}, 'idem-1', career_id=7, club_id=9)
    second = service.audit_mutation('finance_revenue', {'amount':100,'reference':'r1'}, 'idem-1', career_id=7, club_id=9)
    assert first['idempotent'] is False and second['idempotent'] is True
    assert len(service.audit(career_id=7, club_id=9, action='finance_revenue')) == 1
    with pytest.raises(ValueError, match='GATEWAY_ACTION_UNKNOWN'):
        service.validate('not-a-contract', {})
    assert service.validate_batch('finance_revenue', [{'amount':1,'reference':'r2'}])
    with pytest.raises(ValueError, match='GATEWAY_BATCH_LIMIT'):
        service.validate_batch('finance_revenue', [{'amount':1,'reference':'r2'}], max_items=0)
    assert service.record_rpc('finance_revenue', 12)['status'] == 'OK'
    assert service.rollback(first['audit_id'], 'manager', 'correção autorizada')['data_mutation'] is False
    assert service.contract_version() == {'version':'701-1.0','utc':True,'source':'GameState'}
    service.close()
