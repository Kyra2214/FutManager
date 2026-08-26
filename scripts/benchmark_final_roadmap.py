#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path


def timed(connection: sqlite3.Connection, query: str) -> dict:
    started = time.perf_counter()
    count = connection.execute(query).fetchone()[0]
    return {"count": int(count), "elapsed_ms": round((time.perf_counter() - started) * 1000, 3)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    connection = sqlite3.connect(f"file:{args.database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    result = {
        "database": str(args.database),
        "bootstrap_8399_clubs": timed(connection, "SELECT COUNT(*) FROM times"),
        "world_advance_scheduled_matches": timed(connection, "SELECT COUNT(*) FROM matches WHERE status='SCHEDULED'"),
        "single_season_rows": timed(connection, "SELECT COUNT(*) FROM seasons"),
        "multi_season_distinct_years": timed(connection, "SELECT COUNT(DISTINCT season_id) FROM seasons"),
        "integrity": connection.execute("PRAGMA integrity_check").fetchone()[0],
        "foreign_key_errors": len(connection.execute("PRAGMA foreign_key_check").fetchall()),
        "read_only": True,
    }
    connection.close()
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
