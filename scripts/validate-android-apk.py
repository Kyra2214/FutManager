#!/usr/bin/env python3
"""Validate the release database embedded in an Android APK."""

from __future__ import annotations

import argparse
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path

CAREER_TABLES = (
    "manager_selection_assignments",
    "manager_careers",
    "managers",
)
ASSET_DATABASE_PATHS = (
    "assets/public/assets/databases/game.db",
    "assets/databases/game.db",
)


def validate(apk: Path) -> dict[str, object]:
    with zipfile.ZipFile(apk) as archive:
        database_name = next((name for name in ASSET_DATABASE_PATHS if name in archive.namelist()), None)
        if database_name is None:
            raise SystemExit(f"APK does not contain a known GameState asset path: {apk}")
        data = archive.read(database_name)
    with tempfile.NamedTemporaryFile(suffix=".db") as database_file:
        database_file.write(data)
        database_file.flush()
        with sqlite3.connect(database_file.name) as connection:
            counts = {
                table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                for table in CAREER_TABLES
            }
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    result = {"apk": str(apk), "database_asset": database_name, "career_counts": counts, "integrity_check": integrity}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if integrity != "ok" or any(counts.values()):
        raise SystemExit(1)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    args = parser.parse_args()
    validate(args.apk)


if __name__ == "__main__":
    main()
