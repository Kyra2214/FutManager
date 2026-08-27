from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from engine.world.first_division import FIRST_DIVISION_SOURCES

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data/state/game.db"
OUTPUT = Path("/home/ubuntu/futmanager_frontend/docs/membership_checksums.json")


def digest(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


connection = sqlite3.connect(STATE)
source_rows = []
for source in FIRST_DIVISION_SOURCES:
    source_rows.append({
        "country_id": source.country_id,
        "country_code": source.country_code,
        "competition": source.competition_name,
        "season": source.season_label,
        "source_url": source.source_url,
        "clubs": list(source.clubs),
        "club_list_sha256": digest(list(source.clubs)),
    })

ranking_rule = {
    "eligible_sql": "trim(COALESCE(times.nome,''))<>'' AND team_asset_links.crest_asset_id OR team_asset_links.crest_mini_asset_id IS NOT NULL",
    "ranking": "institutional_overall DESC, club_id ASC",
    "capacity": [20, 20, 20, 20],
    "total": 80,
}
report = {
    "schema": "membership-checksums-v1",
    "sources": source_rows,
    "ranking_rule": ranking_rule,
    "ranking_rule_sha256": digest(ranking_rule),
}
OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"source_count": len(source_rows), "ranking_rule_sha256": report["ranking_rule_sha256"], "output": str(OUTPUT)}, ensure_ascii=False))
