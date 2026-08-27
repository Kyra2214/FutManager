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
    result = json.loads(execute("startCareer", json.dumps({
        "managerName": "Teste",
        "careerName": "Teste",
        "age": 30,
        "targetType": "club",
        "targetId": 0,
        "selectedCountryIds": [1],
    }), str(database)))
    assert result["ok"] is False
    assert result["error"] in {"CLUB_NOT_FOUND", "WORLD_COUNTRY_NOT_FOUND"}
print("native_engine_smoke=ok")
