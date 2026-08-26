from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ENGINE_ROOT = Path("/home/ubuntu/brasfoot_engine")
STATE_DATABASE = ENGINE_ROOT / "data/state/game.db"
ASSETS_ROOT = ENGINE_ROOT / "assets"
CLUB_CRESTS = ASSETS_ROOT / "escudos/clubes"
CLUB_MINI_CRESTS = ASSETS_ROOT / "escudos/clubes_mini"
SELECTION_KITS = ASSETS_ROOT / "selecoes/camisas"
MANIFEST_PATH = ASSETS_ROOT / "asset_manifest.json"
REPORT_PATH = ASSETS_ROOT / "asset_linking_report.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as asset:
        for block in iter(lambda: asset.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ENGINE_ROOT).as_posix()


def create_schema(connection: sqlite3.Connection) -> None:
    existing_columns = {
        row[1]: row for row in connection.execute("PRAGMA table_info(team_asset_links)").fetchall()
    }
    if existing_columns and int(existing_columns["crest_mini_asset_id"][3]) == 1:
        existing_links = connection.execute("SELECT COUNT(*) FROM team_asset_links").fetchone()[0]
        if existing_links:
            raise RuntimeError("Migração de links de escudo requer revisão manual: tabela legada contém dados.")
        connection.execute("DROP TABLE team_asset_links")

    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS asset_catalog (
            asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_type TEXT NOT NULL CHECK(asset_type IN ('TEAM_CREST', 'TEAM_CREST_MINI', 'SELECTION_PRIMARY_KIT')),
            source_key TEXT NOT NULL,
            original_relative_path TEXT NOT NULL,
            relative_path TEXT NOT NULL UNIQUE,
            sha256 TEXT NOT NULL,
            mime_type TEXT NOT NULL DEFAULT 'image/png',
            width INTEGER NOT NULL DEFAULT 60,
            height INTEGER NOT NULL DEFAULT 60,
            imported_at TEXT NOT NULL,
            UNIQUE(asset_type, source_key)
        );

        CREATE TABLE IF NOT EXISTS team_asset_links (
            time_id INTEGER PRIMARY KEY REFERENCES times(time_id),
            source_key TEXT NOT NULL UNIQUE,
            crest_asset_id INTEGER REFERENCES asset_catalog(asset_id),
            crest_mini_asset_id INTEGER REFERENCES asset_catalog(asset_id),
            mapping_status TEXT NOT NULL CHECK(mapping_status IN ('COMPLETE', 'FULL_ONLY', 'MINI_ONLY', 'NO_SOURCE_ASSET')),
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS selection_asset_links (
            selecao_id INTEGER PRIMARY KEY REFERENCES selecoes(selecao_id),
            selection_code TEXT NOT NULL UNIQUE,
            crest_asset_id INTEGER REFERENCES asset_catalog(asset_id),
            primary_kit_asset_id INTEGER NOT NULL REFERENCES asset_catalog(asset_id),
            crest_status TEXT NOT NULL CHECK(crest_status IN ('SOURCE_NOT_PROVIDED')),
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_asset_catalog_type_key ON asset_catalog(asset_type, source_key);
        CREATE INDEX IF NOT EXISTS idx_team_asset_links_crest ON team_asset_links(crest_asset_id);
        CREATE INDEX IF NOT EXISTS idx_selection_asset_links_kit ON selection_asset_links(primary_kit_asset_id);
        """
    )


def upsert_asset(
    connection: sqlite3.Connection,
    asset_type: str,
    source_key: str,
    original_path: str,
    asset_path: Path,
    imported_at: str,
) -> int:
    connection.execute(
        """
        INSERT INTO asset_catalog (
            asset_type, source_key, original_relative_path, relative_path, sha256, imported_at
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(relative_path) DO UPDATE SET
            asset_type = excluded.asset_type,
            source_key = excluded.source_key,
            original_relative_path = excluded.original_relative_path,
            sha256 = excluded.sha256,
            imported_at = excluded.imported_at
        """,
        (asset_type, source_key, original_path, relative(asset_path), sha256(asset_path), imported_at),
    )
    row = connection.execute(
        "SELECT asset_id FROM asset_catalog WHERE relative_path = ?", (relative(asset_path),)
    ).fetchone()
    if row is None:
        raise RuntimeError(f"Asset não persistido: {asset_path}")
    return int(row[0])


def main() -> None:
    if not STATE_DATABASE.exists():
        raise FileNotFoundError(f"Banco de estado não encontrado: {STATE_DATABASE}")

    imported_at = datetime.now(timezone.utc).isoformat()
    connection = sqlite3.connect(STATE_DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    create_schema(connection)

    try:
        with connection:
            full_crest_ids = {
                path.stem.casefold(): upsert_asset(
                    connection,
                    "TEAM_CREST",
                    path.stem,
                    f"teams/escudos/{path.name}",
                    path,
                    imported_at,
                )
                for path in sorted(CLUB_CRESTS.glob("*.png"))
            }
            mini_crest_ids = {
                path.stem.casefold(): upsert_asset(
                    connection,
                    "TEAM_CREST_MINI",
                    path.stem,
                    f"teams/escudosMini/{path.name}",
                    path,
                    imported_at,
                )
                for path in sorted(CLUB_MINI_CRESTS.glob("*.png"))
            }
            selection_kit_ids = {
                path.stem.casefold(): upsert_asset(
                    connection,
                    "SELECTION_PRIMARY_KIT",
                    path.stem,
                    f"selecoes/camisas/{path.name}",
                    path,
                    imported_at,
                )
                for path in sorted(SELECTION_KITS.glob("*.png"))
            }

            teams = connection.execute(
                "SELECT time_id, arquivo_origem FROM times ORDER BY time_id"
            ).fetchall()
            team_status_counts = {
                "COMPLETE": 0,
                "FULL_ONLY": 0,
                "MINI_ONLY": 0,
                "NO_SOURCE_ASSET": 0,
            }
            for team in teams:
                source_key = Path(team["arquivo_origem"]).stem
                key = source_key.casefold()
                full_asset_id = full_crest_ids.get(key)
                mini_asset_id = mini_crest_ids.get(key)
                if full_asset_id is not None and mini_asset_id is not None:
                    status = "COMPLETE"
                elif full_asset_id is not None:
                    status = "FULL_ONLY"
                elif mini_asset_id is not None:
                    status = "MINI_ONLY"
                else:
                    status = "NO_SOURCE_ASSET"
                team_status_counts[status] += 1
                connection.execute(
                    """
                    INSERT INTO team_asset_links (
                        time_id, source_key, crest_asset_id, crest_mini_asset_id, mapping_status, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(time_id) DO UPDATE SET
                        source_key = excluded.source_key,
                        crest_asset_id = excluded.crest_asset_id,
                        crest_mini_asset_id = excluded.crest_mini_asset_id,
                        mapping_status = excluded.mapping_status,
                        updated_at = excluded.updated_at
                    """,
                    (team["time_id"], source_key, full_asset_id, mini_asset_id, status, imported_at),
                )

            selections = connection.execute(
                "SELECT selecao_id, codigo FROM selecoes ORDER BY selecao_id"
            ).fetchall()
            for selection in selections:
                code = str(selection["codigo"])
                kit_asset_id = selection_kit_ids.get(code.casefold())
                if kit_asset_id is None:
                    raise RuntimeError(f"Camisa primária ausente para a seleção {selection['selecao_id']}: {code}")
                connection.execute(
                    """
                    INSERT INTO selection_asset_links (
                        selecao_id, selection_code, crest_asset_id, primary_kit_asset_id, crest_status, updated_at
                    ) VALUES (?, ?, NULL, ?, 'SOURCE_NOT_PROVIDED', ?)
                    ON CONFLICT(selecao_id) DO UPDATE SET
                        selection_code = excluded.selection_code,
                        crest_asset_id = NULL,
                        primary_kit_asset_id = excluded.primary_kit_asset_id,
                        crest_status = excluded.crest_status,
                        updated_at = excluded.updated_at
                    """,
                    (selection["selecao_id"], code, kit_asset_id, imported_at),
                )

        report = {
            "generated_at": imported_at,
            "asset_counts": {
                "team_crests": len(full_crest_ids),
                "team_mini_crests": len(mini_crest_ids),
                "selection_primary_kits": len(selection_kit_ids),
            },
            "team_link_status": team_status_counts,
            "selection_links": len(selections),
            "selection_crest_policy": "SOURCE_NOT_PROVIDED",
            "state_database": str(STATE_DATABASE),
        }
        REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        manifest = {
            "generated_at": imported_at,
            "assets_root": "assets",
            "notes": {
                "team_crests": "Escudos originais de teams/escudos.",
                "team_mini_crests": "Escudos originais de teams/escudosMini.",
                "selection_primary_kits": "Uniformes originais de selecoes/camisas; o pacote não fornece escudos de seleções.",
            },
        }
        MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
