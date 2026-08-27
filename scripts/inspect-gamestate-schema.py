#!/usr/bin/env python3
from __future__ import annotations
import sqlite3
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: inspect-gamestate-schema.py GAME_DB")
connection = sqlite3.connect(Path(sys.argv[1]))
for (table,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    columns = [row[1] for row in connection.execute(f"PRAGMA table_info(\"{table}\")")]
    if any(token in table.lower() for token in ("career", "club", "match", "event", "competition", "season", "week", "asset", "time", "selec", "pais", "country")):
        print(f"{table}: {', '.join(columns)}")
