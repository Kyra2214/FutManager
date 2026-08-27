from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data" / "state" / "game.db"
if not STATE.exists():
    STATE = ROOT / "data" / "database" / "game.db"
import sys
sys.path.insert(0, str(ROOT))
from scripts.career_gateway import run


def table_exists(db: sqlite3.Connection, name: str) -> bool:
    return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="futmanager-season-") as folder:
        path = Path(folder) / "season.db"
        shutil.copy2(STATE, path)
        db = sqlite3.connect(path)
        db.row_factory = sqlite3.Row
        report: dict[str, object] = {"database": str(path), "steps": [], "invariants": [], "status": "RUNNING"}

        def step(name: str, action: str, payload: dict | None = None):
            result = run(action, payload or {}, path)
            if result.get("ok") is False:
                raise RuntimeError(f"{name}: {result}")
            report["steps"].append({"name": name, "action": action, "result": result})
            return result

        def invariant(name: str, condition: bool, details: object = None):
            report["invariants"].append({"name": name, "passed": bool(condition), "details": details})
            if not condition:
                raise AssertionError(f"invariant failed: {name}: {details}")

        career = step("create career", "start", {"manager_name": "CI Manager", "nationality": "BR", "age":  thirty_one, "career_name": "CI Season", "target_type": "club", "target_id": 1, "selected_country_ids": [29]})
        club_id = int(career["target_id"])
        before = step("load economy", "economy_summary")
        step("load roster", "current")
        step("bootstrap stadium", "stadium_bootstrap")
        step("bootstrap sponsorship", "sponsor_bootstrap")
        offers = step("read sponsorship offers", "sponsor_summary")
        if offers.get("offers"):
            step("accept sponsorship", "sponsor_accept", {"offer_id": offers["offers"][0]["offer_id"]})
        departments = step("read CT offers", "department_offers")
        if departments.get("items"):
            step("start CT improvement", "department_upgrade", {"department": departments["items"][0]["department"]})
        db.commit()
        after = step("economy after actions", "economy_summary")
        invariant("career owns the selected club", after.get("club_id") == club_id, after)
        invariant("cash change has economic state", after.get("cash") is not None, after)
        step("weekly training", "weekly_training", {"season": 2026, "week": 1, "plan_type": "GENERAL", "load": 50, "seed": 17})
        step("health alerts", "health_alerts")
        step("travel summary", "travel_summary")
        step("weekly advance", "weekly_advance", {"seed": 17})
        step("events", "events_list")
        step("career snapshot", "career_snapshot")
        db.commit()
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = db.execute("PRAGMA foreign_key_check").fetchall()
        invariant("sqlite integrity", integrity == "ok", integrity)
        invariant("foreign keys", not foreign_keys, len(foreign_keys))
        report["status"] = "PASS"
        report["club_id"] = club_id
        report["final_integrity"] = {"integrity_check": integrity, "foreign_key_errors": len(foreign_keys)}
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        return 0


if __name__ == "__main__":
    thirty_one = 31
    raise SystemExit(main())
