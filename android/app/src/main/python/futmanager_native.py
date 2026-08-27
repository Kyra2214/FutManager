"""Chaquopy entry point for the offline FutManager engine."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from engine.manager.career import ManagerService
from engine.world.weekly_cycle import WeeklyWorldCycleService


def _connection(database_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(str(Path(database_path)))
    connection.row_factory = sqlite3.Row
    return connection


def execute(action: str, payload_json: str, database_path: str) -> str:
    payload: dict[str, Any] = json.loads(payload_json or "{}")
    connection = _connection(database_path)
    try:
        if action == "startCareer":
            result = ManagerService(connection).start_career(
                manager_name=payload.get("managerName"),
                nationality=payload.get("nationality"),
                age=payload.get("age"),
                career_name=payload.get("careerName"),
                target_type=payload.get("targetType", "club"),
                target_id=payload.get("targetId"),
                selected_country_ids=payload.get("selectedCountryIds"),
            )
        elif action == "advanceWeek":
            result = WeeklyWorldCycleService(connection).advance_week(payload.get("seed"))
        else:
            raise ValueError(f"NATIVE_ENGINE_ACTION_UNSUPPORTED:{action}")
        return json.dumps({"ok": True, **result}, ensure_ascii=False)
    except Exception as error:
        connection.rollback()
        return json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False)
    finally:
        connection.close()
