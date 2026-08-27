import sqlite3
from pathlib import Path
from engine.world.first_division import resolve_first_division_members

connection = sqlite3.connect(Path(__file__).parents[1] / "data/state/game.db")
for country_id in (3, 72, 97, 11):
    report = resolve_first_division_members(connection, country_id)
    print(country_id, "unmatched=", report["unmatched"])
    print(country_id, "ambiguous=", report["ambiguous"])
    rows = connection.execute("SELECT nome FROM times WHERE pais_id=? ORDER BY nome", (country_id,)).fetchall()
    print(country_id, "sql_sample=", [row[0] for row in rows[:80]])
    print(country_id, "specific=", [row[0] for row in connection.execute("SELECT nome FROM times WHERE pais_id=? AND (lower(nome) LIKE '%brest%' OR lower(nome) LIKE '%marseille%') ORDER BY nome", (country_id,)).fetchall()])
connection.close()
