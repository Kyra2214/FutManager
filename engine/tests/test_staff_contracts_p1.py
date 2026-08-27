from __future__ import annotations

from engine.economy.staff_market import StaffMarketService
from test_staff_market_economy import make_db


def test_staff_preview_requires_explicit_approval_and_records_affinity(tmp_path):
    service = StaffMarketService(make_db(tmp_path))
    available = service.available_staff(1, 'medico')[0]
    preview = service.preview_staff_hire(1, available['staff_id'], 'hire-preview-1')
    assert preview['status'] == 'PENDING'
    assert preview['persisted'] is True
    assert preview['affinity']['medicina'] > 0
    proposal_id = service.connection.execute('SELECT proposal_id FROM staff_hire_proposals WHERE reference=?', ('hire-preview-1',)).fetchone()[0]
    approved = service.approve_staff_hire(1, proposal_id, True)
    assert approved['proposal_id'] == proposal_id
    assert service.connection.execute("SELECT status FROM staff_hire_proposals WHERE proposal_id=?", (proposal_id,)).fetchone()[0] == 'APPROVED'
    service.close()


def test_staff_role_evaluation_absence_and_history_are_persisted(tmp_path):
    service = StaffMarketService(make_db(tmp_path))
    available = service.available_staff(1, 'medico')[0]
    hired = service.hire_staff(1, available['staff_id'])
    changed = service.change_staff_role(1, hired['staff_id'], 'scout', 'role-change-1')
    assert changed['previous_role'] == 'medico'
    evaluation = service.evaluate_staff(1, hired['staff_id'], 84, 'boa integração')
    assert evaluation['score'] == 84
    absence = service.schedule_staff_absence(1, hired['staff_id'], '2026-03-01', '2026-03-05', 'férias')
    assert absence['status'] == 'SCHEDULED'
    history = service.list_staff_history(1, hired['staff_id'])
    assert history and history[0]['event_type'] == 'STAFF_HIRED'
    assert service.connection.execute('SELECT COUNT(*) FROM staff_role_history WHERE reference=?', ('role-change-1',)).fetchone()[0] == 1
    service.close()
