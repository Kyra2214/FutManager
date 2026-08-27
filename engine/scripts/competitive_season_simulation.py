from __future__ import annotations

import json
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "data" / "state" / "game.db"
if not STATE.exists():
    STATE = ROOT / "data" / "database" / "game.db"
sys.path.insert(0, str(ROOT))

from competitions.match_engine import CompetitionService
from manager.career import ManagerService
from scripts.career_gateway import run


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="futmanager-competitive-season-") as folder:
        path = Path(folder) / "season.db"
        shutil.copy2(STATE, path)
        db = sqlite3.connect(path)
        db.row_factory = sqlite3.Row
        report: dict[str, object] = {"database": str(path), "status": "RUNNING", "steps": [], "invariants": []}

        def invariant(name: str, condition: bool, details: object = None) -> None:
            report["invariants"].append({"name": name, "passed": bool(condition), "details": details})
            if not condition:
                raise AssertionError(f"invariant failed: {name}: {details}")

        career = run("start", {"manager_name": "Competitive CI", "nationality": "BR", "age": 31, "career_name": "Competitive Season", "target_type": "club", "target_id": 1, "selected_country_ids": [29, 104, 65, 154]}, path)
        if career.get("ok") is False:
            raise RuntimeError(career)
        report["steps"].append({"name": "create multi-country career", "action": "start", "result": career})
        career_id = int(career["career_id"])

        snapshot = run("parallel_snapshot", {"career_id": career_id, "season_number": 1}, path)
        if snapshot.get("ok") is False:
            raise RuntimeError(snapshot)
        fixtures = [dict(row) for row in db.execute("SELECT * FROM career_parallel_fixtures WHERE career_id=? AND season_number=? ORDER BY fixture_id", (career_id, 1)).fetchall()]
        fixture_count = len(fixtures)
        report["steps"].append({"name": "materialize competitive fixtures", "action": "parallel_snapshot", "result": {"fixture_count": fixture_count, "league": snapshot.get("league")}})
        invariant("four divisions with 80 clubs", snapshot.get("league", {}).get("total_clubs") == 80 and snapshot.get("league", {}).get("division_count") == 4, snapshot.get("league"))
        invariant("double round-robin fixture volume", fixture_count == 1520, fixture_count)

        competition = db.execute("SELECT competition_id, season_id FROM competitions ORDER BY competition_id LIMIT 1").fetchone()
        if competition is None:
            competition_service = CompetitionService(db)
            season = db.execute("SELECT season_id FROM seasons WHERE year=?", (2026,)).fetchone()
            season_id = int(season["season_id"]) if season else competition_service.create_season(2026)
            club_ids = sorted({int(fixture["home_club_id"]) for fixture in fixtures} | {int(fixture["away_club_id"]) for fixture in fixtures})
            competition_id = competition_service.create_competition("Liga Paralela CI", season_id, club_ids, type_="LEAGUE", format_="ROUND_ROBIN")
            competition = db.execute("SELECT competition_id, season_id FROM competitions WHERE competition_id=?", (competition_id,)).fetchone()
        engine = CompetitionService(db)
        played = 0
        for fixture in fixtures:
            fixture_id = int(fixture["fixture_id"])
            db.execute("INSERT INTO matches(competition_id,season_id,match_date,round,home_club_id,away_club_id,status,seed,venue_type,weather,security_level) VALUES(?,?,?,?,?,?,?,?,?,?,?)", (int(competition["competition_id"]), int(competition["season_id"]), fixture["scheduled_date"], int(fixture["matchday"]), int(fixture["home_club_id"]), int(fixture["away_club_id"]), "SCHEDULED", fixture_id, "HOME", "UNKNOWN", "STANDARD"))
            match_id = int(db.execute("SELECT last_insert_rowid()").fetchone()[0])
            result = engine.play(match_id, seed=fixture_id, managed_transaction=False)
            parallel = run("parallel_result", {"career_id": career_id, "fixture_id": fixture_id, "home_goals": result.home_goals, "away_goals": result.away_goals}, path)
            if parallel.get("ok") is False:
                raise RuntimeError({"fixture_id": fixture_id, "result": parallel})
            played += 1
            if played % 200 == 0:
                report["steps"].append({"name": f"played {played} fixtures", "action": "match_engine + parallel_result", "result": {"played": played}})
        db.commit()

        final = run("parallel_snapshot", {"career_id": career_id, "season_number": 1}, path)
        report["steps"].append({"name": "final competitive snapshot", "action": "parallel_snapshot", "result": {"fixture_count": final.get("fixture_count"), "played_count": final.get("played_count")}})
        invariant("all fixtures played", final.get("played_count") == fixture_count, {"fixture_count": fixture_count, "played_count": final.get("played_count")})
        invariant("standings have 80 rows", len(final.get("standings", [])) == 80, len(final.get("standings", [])))
        invariant("sqlite integrity", db.execute("PRAGMA integrity_check").fetchone()[0] == "ok", db.execute("PRAGMA integrity_check").fetchone()[0])
        invariant("foreign keys", not db.execute("PRAGMA foreign_key_check").fetchall(), None)
        report["status"] = "PASS"
        report["fixture_count"] = fixture_count
        report["played_count"] = played
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
