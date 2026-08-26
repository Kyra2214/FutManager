import json
import sqlite3

DATABASE = "file:/home/ubuntu/brasfoot_engine/data/state/game.db?mode=ro"

connection = sqlite3.connect(DATABASE, uri=True)
connection.row_factory = sqlite3.Row

report = {
    "integrity_check": connection.execute("PRAGMA integrity_check").fetchone()[0],
    "foreign_key_issues": connection.execute("PRAGMA foreign_key_check").fetchall(),
    "team_links": connection.execute("SELECT COUNT(*) FROM team_asset_links").fetchone()[0],
    "team_status": [
        dict(row)
        for row in connection.execute(
            "SELECT mapping_status, COUNT(*) AS total FROM team_asset_links GROUP BY mapping_status ORDER BY mapping_status"
        ).fetchall()
    ],
    "selection_links": connection.execute("SELECT COUNT(*) FROM selection_asset_links").fetchone()[0],
    "selection_crest_status": [
        dict(row)
        for row in connection.execute(
            "SELECT crest_status, COUNT(*) AS total FROM selection_asset_links GROUP BY crest_status"
        ).fetchall()
    ],
    "unlinked_teams": [
        dict(row)
        for row in connection.execute(
            """
            SELECT link.mapping_status, team.time_id, team.nome, team.arquivo_origem
            FROM team_asset_links link
            INNER JOIN times team ON team.time_id = link.time_id
            WHERE link.mapping_status <> 'COMPLETE'
            ORDER BY link.mapping_status, team.time_id
            """
        ).fetchall()
    ],
    "orphan_team_crests": [
        dict(row)
        for row in connection.execute(
            """
            SELECT asset.relative_path, asset.source_key
            FROM asset_catalog asset
            LEFT JOIN team_asset_links link ON link.crest_asset_id = asset.asset_id
            WHERE asset.asset_type = 'TEAM_CREST' AND link.time_id IS NULL
            ORDER BY asset.relative_path
            """
        ).fetchall()
    ],
    "example_team_link": dict(
        connection.execute(
            """
            SELECT team.time_id, team.nome, link.mapping_status,
                   full_asset.relative_path AS crest_path, mini_asset.relative_path AS mini_crest_path
            FROM times team
            INNER JOIN team_asset_links link ON link.time_id = team.time_id
            LEFT JOIN asset_catalog full_asset ON full_asset.asset_id = link.crest_asset_id
            LEFT JOIN asset_catalog mini_asset ON mini_asset.asset_id = link.crest_mini_asset_id
            WHERE team.arquivo_origem = '07vestur_fro.ban'
            """
        ).fetchone()
    ),
}

connection.close()
print(json.dumps(report, ensure_ascii=False, indent=2))
