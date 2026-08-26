import sqlite3

DB = "/home/ubuntu/brasfoot_engine/data/state/game.db"
NAMES = {
    "times",
    "competitions",
    "seasons",
    "matches",
    "standings",
    "fixtures",
    "competition_phases",
    "competition_rounds",
    "club_stats",
    "competition_entries",
    "team_competition_stats",
    "manager_careers",
}

connection = sqlite3.connect(DB)
rows = connection.execute(
    "SELECT name, sql FROM sqlite_master WHERE type = 'table' ORDER BY name"
).fetchall()
print("TABLES:", ", ".join(row[0] for row in rows))
for name, statement in rows:
    if name in NAMES:
        print(f"\n--- {name} ---\n{statement}")
connection.close()
