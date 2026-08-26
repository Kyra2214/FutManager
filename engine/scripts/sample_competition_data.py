import sqlite3

DB = "/home/ubuntu/brasfoot_engine/data/state/game.db"
TABLES = [
    "seasons",
    "competitions",
    "competition_entries",
    "competition_phases",
    "competition_rounds",
    "fixtures",
    "matches",
    "team_competition_stats",
]

connection = sqlite3.connect(DB)
connection.row_factory = sqlite3.Row
for table in TABLES:
    count = connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
    print(f"{table}: {count}")
    if count:
        for row in connection.execute(f"SELECT * FROM {table} LIMIT 3").fetchall():
            print(dict(row))
connection.close()
