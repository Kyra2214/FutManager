import sqlite3
from engine.management.board import BoardService

def test_board_quorum_conflict_minutes_history_and_pending():
    service = BoardService(sqlite3.connect(':memory:'))
    first = service.add_member(1, 'Ana', 'PRESIDENT', '2026-01-01', '2028-12-31')
    second = service.add_member(1, 'Bruno', 'DIRECTOR', '2026-01-01', '2027-12-31')
    decision = service.create_decision(1, 'upgrade', required_quorum=2)
    assert service.vote(decision, first, 'YES')['accepted'] is True
    assert service.vote(decision, second, 'YES', conflict=True)['accepted'] is False
    assert service.resolve(decision)['status'] == 'PENDING'
    assert service.vote(decision, second, 'YES')['accepted'] is True
    assert service.resolve(decision)['status'] == 'APPROVED'
    assert service.minutes(decision, 'Ata aprovada') == 1
    assert service.history(1)[0]['status'] == 'APPROVED'
    assert service.pending(1) == []
    service.close()
