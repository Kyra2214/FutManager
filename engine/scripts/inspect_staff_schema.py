import json
import sqlite3

KEYWORDS = ("staff", "coach", "trainer", "medical", "doctor", "scout", "injur", "health", "commission", "training", "department")
connection = sqlite3.connect("file:/home/ubuntu/brasfoot_engine/data/state/game.db?mode=ro", uri=True)
connection.row_factory = sqlite3.Row
tables = [row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
report = {}
for table in tables:
    if any(keyword in table.lower() for keyword in KEYWORDS):
        report[table] = {
            "count": connection.execute(f"SELECT COUNT(*) AS total FROM [{table}]").fetchone()["total"],
            "columns": [row["name"] for row in connection.execute(f"PRAGMA table_info([{table}])")],
        }
connection.close()
print(json.dumps(report, ensure_ascii=False, indent=2))
