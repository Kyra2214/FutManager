import json
import sqlite3

DATABASE = "file:/home/ubuntu/brasfoot_engine/data/state/game.db?mode=ro"

connection = sqlite3.connect(DATABASE, uri=True)
connection.row_factory = sqlite3.Row
report = {}
for table in ("managers", "manager_careers", "manager_contracts", "manager_national_team_assignments"):
    try:
        report[table] = {
            "count": connection.execute(f"SELECT COUNT(*) AS total FROM {table}").fetchone()["total"],
            "columns": [dict(row) for row in connection.execute(f"PRAGMA table_info({table})").fetchall()],
        }
    except sqlite3.Error as error:
        report[table] = {"error": str(error)}
connection.close()
print(json.dumps(report, ensure_ascii=False, indent=2))
