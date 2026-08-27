#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path


def inspect(path: Path) -> dict:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
    tables = [row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    connection.close()
    return {"path": str(path), "sha256": digest, "integrity_check": integrity, "foreign_key_errors": len(foreign_keys), "tables": tables}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("state_db", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    exported = args.output_dir / "game_state.sqlite"
    shutil.copy2(args.state_db, exported)
    manifest = {"format": "futmanager-state-export-v1", "contains_secrets": False, "source": inspect(args.state_db), "export": inspect(exported)}
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
