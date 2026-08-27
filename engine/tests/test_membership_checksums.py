from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPORT = Path("/home/ubuntu/futmanager_frontend/docs/membership_checksums.json")


def _digest(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_membership_checksum_report_is_complete_and_deterministic() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    assert report["schema"] == "membership-checksums-v1"
    assert len(report["sources"]) == 6
    assert {source["country_code"] for source in report["sources"]} >= {"BRA", "ITA", "ESP", "POR", "GER", "FRA"}
    assert all(source["club_list_sha256"] == _digest(source["clubs"]) for source in report["sources"])
    assert report["ranking_rule"]["capacity"] == [20, 20, 20, 20]
    assert report["ranking_rule"]["total"] == 80
    assert report["ranking_rule"]["ranking"] == "institutional_overall DESC, club_id ASC"
    assert report["ranking_rule_sha256"] == _digest(report["ranking_rule"])
