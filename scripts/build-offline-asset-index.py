#!/usr/bin/env python3
"""Generate the local entity-id -> packaged asset map from the canonical GameState."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path


def columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: build-offline-asset-index.py GAME_DB OUTPUT_JSON")
    database, output = map(Path, sys.argv[1:])
    connection = sqlite3.connect(database)
    catalog = {
        int(asset_id): str(path).replace("\\", "/")
        for asset_id, path in connection.execute(
            "SELECT asset_id, relative_path FROM asset_catalog"
        )
    }
    result: dict[str, dict[str, str | int | None]] = {}
    team_columns = columns(connection, "team_asset_links")
    if {"time_id", "crest_asset_id"} <= team_columns:
        for team_id, crest_id, mini_id in connection.execute(
            "SELECT time_id, crest_asset_id, crest_mini_asset_id FROM team_asset_links"
        ):
            asset_id = crest_id or mini_id
            result[f"team:{team_id}"] = {
                "entityId": int(team_id),
                "kind": "club",
                "path": catalog.get(int(asset_id)) if asset_id else None,
            }
    selection_columns = columns(connection, "selection_asset_links")
    if {"selecao_id", "primary_kit_asset_id"} <= selection_columns:
        for selection_id, kit_id in connection.execute(
            "SELECT selecao_id, primary_kit_asset_id FROM selection_asset_links"
        ):
            result[f"selection:{selection_id}"] = {
                "entityId": int(selection_id),
                "kind": "selection",
                "path": catalog.get(int(kit_id)) if kit_id else None,
            }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"Generated {len(result)} asset references in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
