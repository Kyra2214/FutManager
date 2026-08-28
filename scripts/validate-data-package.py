#!/usr/bin/env python3
"""Validate the remote data package before an Android first-run installation."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path

CAREER_TABLES = ("manager_selection_assignments", "manager_careers", "managers")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(package: Path, manifest_path: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual_hash = sha256(package)
    expected_hash = manifest.get("packageSha256")
    if expected_hash and actual_hash != expected_hash:
        raise SystemExit(f"package SHA-256 mismatch: expected {expected_hash}, got {actual_hash}")
    expected_bytes = manifest.get("packageBytes")
    if expected_bytes is not None and package.stat().st_size != expected_bytes:
        raise SystemExit("package byte count does not match manifest")

    with zipfile.ZipFile(package) as archive:
        database_name = "database/game.db"
        if database_name not in archive.namelist():
            raise SystemExit(f"missing {database_name}")
        database_bytes = archive.read(database_name)
        required = {"offline-countries.json", "offline-asset-index.json"}
        missing = sorted(name for name in required if name not in archive.namelist())
        if missing:
            raise SystemExit(f"missing package files: {missing}")

    with tempfile.NamedTemporaryFile(suffix=".db") as database_file:
        database_file.write(database_bytes)
        database_file.flush()
        with sqlite3.connect(database_file.name) as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            counts = {
                table: connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                for table in CAREER_TABLES
            }

    result = {
        "package": str(package),
        "package_sha256": actual_hash,
        "package_bytes": package.stat().st_size,
        "database_bytes": len(database_bytes),
        "integrity_check": integrity,
        "career_counts": counts,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if integrity != "ok" or any(counts.values()):
        raise SystemExit(1)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    validate(args.package, args.manifest)


if __name__ == "__main__":
    main()
