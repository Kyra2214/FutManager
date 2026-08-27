#!/usr/bin/env python3
"""Generate the offline country catalog from the engine's canonical sources."""
from __future__ import annotations

import json
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: build-offline-country-index.py ENGINE_ROOT OUTPUT_JSON")
engine_root, output = map(Path, sys.argv[1:])
sys.path.insert(0, str(engine_root))
from engine.world.first_division import FIRST_DIVISION_SOURCES  # type: ignore[import-not-found]

countries = [
    {
        "countryId": source.country_id,
        "name": source.country_code,
        "code": source.country_code,
        "clubCount": len(source.clubs),
        "firstDivisionClubCount": len(source.clubs),
        "firstDivisionName": source.competition_name,
        "supported": True,
    }
    for source in FIRST_DIVISION_SOURCES
]
Path(output).parent.mkdir(parents=True, exist_ok=True)
Path(output).write_text(json.dumps(countries, ensure_ascii=False, indent=2) + "\n")
print(f"Generated {len(countries)} offline country entries in {output}")
