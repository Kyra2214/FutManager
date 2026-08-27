from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Priority = Literal["P0", "P1", "P2"]


class RoadmapGateError(RuntimeError):
    """Raised when a roadmap priority is attempted before its dependencies are ready."""


@dataclass(frozen=True)
class RoadmapGate:
    gate_path: Path

    @classmethod
    def from_engine_root(cls, engine_root: Path) -> "RoadmapGate":
        return cls(engine_root.parent / "futmanager_frontend" / "roadmap_gate.json")

    def read(self) -> dict:
        if not self.gate_path.exists():
            raise RoadmapGateError(f"ROADMAP_GATE_NOT_FOUND:{self.gate_path}")
        try:
            payload = json.loads(self.gate_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RoadmapGateError("ROADMAP_GATE_INVALID") from error
        if payload.get("sql_game_state_source_of_truth") is not True:
            raise RoadmapGateError("SQL_GAMESTATE_SOURCE_OF_TRUTH_REQUIRED")
        if payload.get("p0_gate") not in {"OPEN", "CLOSED"}:
            raise RoadmapGateError("ROADMAP_GATE_STATUS_INVALID")
        return payload

    def assert_front_allowed(self, front: int) -> None:
        payload = self.read()
        dependencies = payload.get("front_dependencies", {}).get(str(front))
        if dependencies is None:
            raise RoadmapGateError(f"ROADMAP_FRONT_NOT_FOUND:{front}")
        statuses = payload.get("front_statuses", {})
        missing = [dependency for dependency in dependencies if statuses.get(str(dependency)) != "CONSOLIDATED"]
        if missing:
            raise RoadmapGateError(f"FRONT_{front}_BLOCKED_DEPENDENCIES:{','.join(map(str, missing))}")
        priority = payload.get("front_priorities", {}).get(str(front))
        if priority in {"P0", "P1", "P2"}:
            self.assert_allowed(priority)

    def assert_allowed(self, priority: Priority) -> None:
        payload = self.read()
        if priority == "P0":
            return
        if payload["p0_gate"] != "OPEN":
            raise RoadmapGateError(f"{priority}_BLOCKED_UNTIL_P0_CONSOLIDATED")
        if priority == "P2" and payload.get("p1_gate") != "OPEN":
            raise RoadmapGateError("P2_BLOCKED_UNTIL_P1_STABLE")

    def status(self) -> dict:
        payload = self.read()
        p0_fronts = payload.get("p0_fronts", [])
        consolidated = sum(front.get("status") == "CONSOLIDATED" for front in p0_fronts)
        return {
            "p0_gate": payload["p0_gate"],
            "p1_gate": payload.get("p1_gate", "CLOSED"),
            "p1_p2_blocked": payload["p0_gate"] != "OPEN",
            "p0_fronts": len(p0_fronts),
            "p0_consolidated": consolidated,
            "sql_game_state_source_of_truth": True,
        }
