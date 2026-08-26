from datetime import date

import pytest

from engine.core.domain_errors import DomainErrorCode, error_code
from engine.core.execution import ExecutionContext


def test_execution_context_round_trips_without_game_state():
    context = ExecutionContext("tick-1", date(2026, 8, 26), 2026, 34, 77)
    assert ExecutionContext.from_dict(context.to_dict()) == context
    assert context.to_dict()["scope"] == "WORLD"


@pytest.mark.parametrize(
    "kwargs, error",
    [
        ({"tick_id": "", "current_date": date(2026, 1, 1), "season": 2026, "week": 1, "seed": None}, "TICK_ID_REQUIRED"),
        ({"tick_id": "x", "current_date": date(2026, 1, 1), "season": -1, "week": 1, "seed": None}, "EXECUTION_PERIOD_INVALID"),
        ({"tick_id": "x", "current_date": date(2026, 1, 1), "season": 2026, "week": 1, "seed": None, "scope": "INVALID"}, "EXECUTION_SCOPE_INVALID"),
    ],
)
def test_execution_context_rejects_invalid_values(kwargs, error):
    with pytest.raises(ValueError, match=error):
        ExecutionContext(**kwargs)


def test_domain_error_catalog_has_stable_serialization():
    assert error_code(DomainErrorCode.IMMUTABLE_BASE_DATABASE) == "IMMUTABLE_BASE_DATABASE"
    assert error_code("WEEK_OUT_OF_SEQUENCE") == "WEEK_OUT_OF_SEQUENCE"


def test_read_and_command_boundaries_are_explicit():
    from engine.core.contracts import CommandService, ContractBoundary, ReadRepository

    assert ReadRepository is not None
    assert CommandService is not None
    assert ContractBoundary().source_of_truth == "SQL/GameState"
    assert ContractBoundary().frontend_boundary == "tRPC/Gateway"
