from __future__ import annotations

import sqlite3

import pytest

from engine.core.domain_errors import DomainError
from engine.core.p1_telemetry_contract import (
    audit_p1_telemetry,
    ensure_p1_telemetry_registry,
    read_p1_telemetry_events,
    record_p1_telemetry_event,
    validate_p1_telemetry,
)


def connection() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    ensure_p1_telemetry_registry(c)
    return c


def test_contracts_are_bootstrapped_and_auditable() -> None:
    c = connection()
    assert validate_p1_telemetry(c, 1111)["status"] == "VALID"
    audit = audit_p1_telemetry(c)
    assert audit["status"] == "VALID"
    assert audit["telemetry_count"] == 10


def test_event_record_is_idempotent_and_read_is_bounded() -> None:
    c = connection()
    first = record_p1_telemetry_event(c, "tick-1", "career.weekly_tick", {"result": "ok"}, 7, 1, 3, "AUTHORIZED_SQL_SERVICE")
    second = record_p1_telemetry_event(c, "tick-1", "career.weekly_tick", {"result": "ok"}, 7, 1, 3, "AUTHORIZED_SQL_SERVICE")
    assert first["event_id"] == second["event_id"]
    assert len(read_p1_telemetry_events(c, career_id=7, limit=999)) == 1
    assert read_p1_telemetry_events(c, limit=999)[0]["payload_json"] == {"result": "ok"}


def test_event_mutation_requires_authorized_sql_service() -> None:
    c = connection()
    with pytest.raises(DomainError):
        record_p1_telemetry_event(c, "blocked", "career.event", {}, actor="FRONTEND")
