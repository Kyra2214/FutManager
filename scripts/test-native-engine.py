#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
import sys

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "android/app/src/main/python"))
from futmanager_native import execute  # noqa: E402

source = Path(sys.argv[1])
with tempfile.TemporaryDirectory(prefix="futmanager-native-test-") as directory:
    database = Path(directory) / "game.db"
    shutil.copy2(source, database)
    dashboard = json.loads(execute("getDashboard", "{}", str(database)))
    assert dashboard["ok"] is True
    assert "competitions" in dashboard and "upcomingFixtures" in dashboard
    if dashboard["upcomingFixtures"]:
        target_match = dashboard["upcomingFixtures"][0].get("matchId")
        if target_match:
            travel = json.loads(execute("advanceUntilMatch", json.dumps({"matchId": target_match}), str(database)))
            assert travel["ok"] is True
            assert travel["status"] == "READY_FOR_CONTROLLED_MATCH"
    invalid_start = json.loads(execute("startCareer", json.dumps({
        "managerName": "Teste",
        "careerName": "Teste",
        "age": 30,
        "targetType": "club",
        "targetId": 0,
        "selectedCountryIds": [1],
    }), str(database)))
    assert invalid_start["ok"] is False
    assert invalid_start["error"] in {"CLUB_NOT_FOUND", "WORLD_COUNTRY_NOT_FOUND"}
    invalid_match = json.loads(execute("playControlledMatch", json.dumps({"matchId": 0}), str(database)))
    assert invalid_match["ok"] is False
    assert invalid_match["error"] == "MATCH_ID_REQUIRED"
print("native_engine_smoke=ok")
