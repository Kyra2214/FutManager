from __future__ import annotations

import sqlite3

from engine.sports.cycle import SportStateStore
from engine.sports.health import HealthService


def make_health():
    con = sqlite3.connect(':memory:')
    con.executescript('''
      CREATE TABLE times(time_id INTEGER PRIMARY KEY);
      CREATE TABLE jogadores(jogador_id INTEGER PRIMARY KEY,nome TEXT,idade INTEGER);
      CREATE TABLE jogador_time(jogador_id INTEGER,time_id INTEGER);
      CREATE TABLE staff_members(staff_id INTEGER PRIMARY KEY,club_id INTEGER,role TEXT,level INTEGER,status TEXT);
      INSERT INTO times VALUES(1); INSERT INTO jogadores VALUES(10,'Atleta',24); INSERT INTO jogador_time VALUES(10,1);
    ''')
    SportStateStore(con).ensure_player(10, 1)
    return HealthService(con)


def test_health_catalog_injury_preview_reassessment_and_recovery():
    service = make_health()
    assert len(service.injury_catalog()) == 3
    injury = service.register_injury(1, 10, 'muscular', 'MINOR', 2026, 1, seed=4)
    preview = service.preview_return(1, 10)
    assert preview['available'] is False and preview['persisted'] is False
    reassessment = service.schedule_reassessment(1, 10, '2026-02-01', 'reavaliar')
    assert reassessment['status'] == 'SCHEDULED'
    assert service.alerts(1)[0]['alert_type'] == 'NEW_INJURY'
    recovered = service.recover(1, 100)
    assert recovered[0]['status'] == 'RETURNED'
    assert service.preview_return(1, 10)['available'] is True
    service.close()


def test_health_recurrence_is_recorded_after_previous_injury():
    service = make_health()
    first = service.register_injury(1, 10, 'ankle', 'MINOR', 2026, 1, seed=1)
    service.recover(1, 100)
    second = service.register_injury(1, 10, 'ankle', 'MINOR', 2026, 2, seed=1)
    count = service.connection.execute('SELECT COUNT(*) FROM injury_relapses WHERE player_id=?', (10,)).fetchone()[0]
    assert second['injury_id'] > first['injury_id'] and count == 1
    service.close()
