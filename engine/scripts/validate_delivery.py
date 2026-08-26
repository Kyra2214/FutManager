from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect(database: Path, immutable: bool = False) -> dict:
    connection = sqlite3.connect(database)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_key_issues = connection.execute("PRAGMA foreign_key_check").fetchall()
        table_count = connection.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    finally:
        connection.close()
    current_hash = sha256(database)
    result = {
        "path": str(database),
        "sha256": current_hash,
        "integrity_check": integrity,
        "foreign_key_check_count": len(foreign_key_issues),
        "table_count": int(table_count),
    }
    if immutable:
        manifest = database.with_suffix(database.suffix + ".sha256")
        expected_hash = manifest.read_text(encoding="utf-8").split()[0]
        result["manifest_sha256"] = expected_hash
        result["manifest_matches"] = current_hash == expected_hash
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida os bancos canônicos do FutManager/Brasfoot.")
    parser.add_argument("--base", type=Path, default=ROOT / "data/database/game.db")
    parser.add_argument("--state", type=Path, default=ROOT / "data/state/game.db")
    args = parser.parse_args()
    result = {"base": inspect(args.base, immutable=True), "state": inspect(args.state, immutable=False)}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if any(item["integrity_check"] != "ok" or item["foreign_key_check_count"] for item in result.values()) or not result["base"].get("manifest_matches", False):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
