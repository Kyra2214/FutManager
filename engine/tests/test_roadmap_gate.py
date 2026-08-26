import json
from pathlib import Path

import pytest

from engine.core.roadmap_gate import RoadmapGate, RoadmapGateError


def write_gate(tmp_path: Path, **changes) -> Path:
    payload = {
        "p0_gate": "CLOSED",
        "p1_gate": "CLOSED",
        "sql_game_state_source_of_truth": True,
        "p0_fronts": [{"front": 1, "status": "PENDING"}],
    }
    payload.update(changes)
    path = tmp_path / "roadmap_gate.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_p0_allowed_but_p1_and_p2_blocked_until_p0_is_open(tmp_path: Path):
    gate = RoadmapGate(write_gate(tmp_path))
    gate.assert_allowed("P0")
    with pytest.raises(RoadmapGateError, match="P1_BLOCKED"):
        gate.assert_allowed("P1")
    with pytest.raises(RoadmapGateError, match="P2_BLOCKED"):
        gate.assert_allowed("P2")


def test_p1_requires_open_p0_and_p2_requires_open_p1(tmp_path: Path):
    gate = RoadmapGate(write_gate(tmp_path, p0_gate="OPEN", p1_gate="CLOSED", p0_fronts=[{"front": 1, "status": "CONSOLIDATED"}]))
    gate.assert_allowed("P1")
    with pytest.raises(RoadmapGateError, match="P2_BLOCKED"):
        gate.assert_allowed("P2")
    gate_open = RoadmapGate(write_gate(tmp_path, p0_gate="OPEN", p1_gate="OPEN", p0_fronts=[{"front": 1, "status": "CONSOLIDATED"}]))
    gate_open.assert_allowed("P2")


def test_front_dependencies_block_until_all_dependencies_are_consolidated(tmp_path: Path):
    payload = {
        "p0_gate": "CLOSED",
        "p1_gate": "CLOSED",
        "sql_game_state_source_of_truth": True,
        "front_priorities": {"1": "P0", "2": "P0", "6": "P1"},
        "front_dependencies": {"1": [], "2": [1], "6": [2]},
        "front_statuses": {"1": "PENDING", "2": "PENDING"},
    }
    gate = RoadmapGate(write_gate(tmp_path, **payload))
    with pytest.raises(RoadmapGateError, match="FRONT_2_BLOCKED_DEPENDENCIES:1"):
        gate.assert_front_allowed(2)
    payload["front_statuses"]["1"] = "CONSOLIDATED"
    Path(gate.gate_path).write_text(json.dumps(payload), encoding="utf-8")
    gate.assert_front_allowed(2)
    with pytest.raises(RoadmapGateError, match="FRONT_6_BLOCKED_DEPENDENCIES:2"):
        gate.assert_front_allowed(6)
    with pytest.raises(RoadmapGateError, match="ROADMAP_FRONT_NOT_FOUND"):
        gate.assert_front_allowed(99)


def test_gate_requires_sql_game_state_source_of_truth(tmp_path: Path):
    gate = RoadmapGate(write_gate(tmp_path, sql_game_state_source_of_truth=False))
    with pytest.raises(RoadmapGateError, match="SOURCE_OF_TRUTH"):
        gate.assert_allowed("P0")
