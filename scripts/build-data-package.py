#!/usr/bin/env python3
"""Build the versioned data package consumed by the hybrid Android app."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

EDITORIAL_ASSETS = (
    "futmanager-program-texture.jpg",
    "futmanager-stadium-editorial.jpg",
    "futmanager-training.jpg",
    "futmanager-mark.png",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, check=True, env=env)


def copy_tree(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(source, destination)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine-root", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args()

    engine_root = args.engine_root.resolve()
    asset_root = args.asset_root.resolve()
    source_database = engine_root / "data/state/game.db"
    source_shields = engine_root / "assets/escudos"
    release_seed = Path(__file__).with_name("release_seed.py")
    asset_index_script = Path(__file__).with_name("build-offline-asset-index.py")
    country_index_script = Path(__file__).with_name("build-offline-country-index.py")
    if not source_database.is_file():
        raise SystemExit(f"GameState não encontrado: {source_database}")
    if not source_shields.is_dir():
        raise SystemExit(f"Escudos não encontrados: {source_shields}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="futmanager-data-package-") as temporary:
        root = Path(temporary)
        stage = root / "stage"
        staged_database = stage / "database/game.db"
        run(["python3", str(release_seed), "sanitize", str(source_database), str(staged_database)])
        copy_tree(source_shields, stage / "assets/escudos")
        for asset_name in EDITORIAL_ASSETS:
            source = asset_root / asset_name
            if not source.is_file():
                raise SystemExit(f"Asset editorial não encontrado: {source}")
            copy_tree(source, stage / "app" / asset_name)
        environment = {**__import__("os").environ, "PYTHONPATH": f"{engine_root.parent}:{engine_root}"}
        run(["python3", str(asset_index_script), str(staged_database), str(stage / "offline-asset-index.json")], env=environment)
        run(["python3", str(country_index_script), str(engine_root), str(stage / "offline-countries.json")], env=environment)

        package = args.output_dir / f"futmanager-data-v{args.version}.zip"
        with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(path for path in stage.rglob("*") if path.is_file()):
                relative = path.relative_to(stage).as_posix()
                info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        manifest = {
            "format": 1,
            "version": args.version,
            "packageUrl": f"{args.base_url.rstrip('/')}/{package.name}",
            "packageSha256": sha256(package),
            "packageBytes": package.stat().st_size,
            "databaseSha256": sha256(staged_database),
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        (args.output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
