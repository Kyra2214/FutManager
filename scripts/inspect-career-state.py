#!/usr/bin/env python3
from __future__ import annotations
import sqlite3
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: inspect-career-state.py GAME_DB")
connection = sqlite3.connect(Path(sys.argv[1]))
for table in ("manager_careers", "world_state", "seasons"):
    print(f"--- {table} ---")
    try:
        for row in connection.execute(f"SELECT * FROM {table} LIMIT 3"):
            print(tuple(row))
    except sqlite3.Error as error:
        print(f"ERROR {error}")
