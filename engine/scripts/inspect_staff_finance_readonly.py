import json
import sqlite3

db = sqlite3.connect("file:/home/ubuntu/brasfoot_engine/data/state/game.db?mode=ro", uri=True)
db.row_factory = sqlite3.Row
career = db.execute("SELECT current_club_id FROM manager_careers WHERE status = 'ACTIVE' ORDER BY updated_at DESC LIMIT 1").fetchone()
club_id = career["current_club_id"] if career else None
tables = {row["name"] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
result = {"club_id": club_id, "tables": {}}
for table in ("club_finances", "club_economic_state", "financial_ledger", "logical_clock"):
    if table in tables:
        if table == "financial_ledger" and club_id is not None:
            rows = db.execute("SELECT category, amount, description, date FROM financial_ledger WHERE club_id = ? ORDER BY ledger_id DESC LIMIT 5", (club_id,)).fetchall()
        else:
            rows = db.execute(f"SELECT * FROM [{table}]" + (" WHERE club_id = ?" if club_id is not None and table in {"club_finances", "club_economic_state"} else "") + " LIMIT 5", (club_id,) if club_id is not None and table in {"club_finances", "club_economic_state"} else ()).fetchall()
        result["tables"][table] = [dict(row) for row in rows]
if club_id is not None:
    team_columns = [row["name"] for row in db.execute("PRAGMA table_info(times)")]
    team = db.execute("SELECT * FROM times WHERE time_id = ?", (club_id,)).fetchone()
    result["team_columns"] = team_columns
    result["team_record"] = dict(team) if team else None
db.close()
print(json.dumps(result, ensure_ascii=False, indent=2))
