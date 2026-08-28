#!/usr/bin/env python3
"""Validate the hybrid Android package contract."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

FORBIDDEN_PREFIXES = (
    "assets/public/assets/databases/",
    "assets/public/assets/escudos/",
    "assets/public/assets/app/",
)


def validate(apk: Path) -> dict[str, object]:
    with zipfile.ZipFile(apk) as archive:
        names = set(archive.namelist())
        manifest_name = "assets/public/assets/offline-manifest.json"
        if manifest_name not in names:
            raise SystemExit(f"APK does not contain the hybrid data manifest: {apk}")
        manifest = json.loads(archive.read(manifest_name).decode("utf-8"))
        if manifest.get("source") != "remote-data-package" or not manifest.get("requiresInitialDownload"):
            raise SystemExit("APK hybrid manifest does not require remote initial data")
        forbidden = sorted(name for name in names if name.startswith(FORBIDDEN_PREFIXES))
        if forbidden:
            raise SystemExit(f"APK contains forbidden heavy data paths: {forbidden[:5]}")
    result = {
        "apk": str(apk),
        "mode": "hybrid",
        "manifest": manifest,
        "forbidden_heavy_paths": [],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    args = parser.parse_args()
    validate(args.apk)


if __name__ == "__main__":
    main()
