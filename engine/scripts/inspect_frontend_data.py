import json
import sqlite3

DATABASE = "file:/home/ubuntu/brasfoot_engine/data/state/game.db?mode=ro"
TABLES = [
    "times", "jogadores", "jogador_time", "club_profiles", "club_finances", "finance_ledger",
    "stadiums", "club_stadiums", "training_centers", "club_training_centers", "club_reputation",
    "team_squads", "injuries", "manager_careers", "manager_selection_assignments",
]

connection = sqlite3.connect(DATABASE, uri=True)
connection.row_factory = sqlite3.Row
report = {}
for table in TABLES:
    try:
        report[table] = {
            "count": connection.execute(f"SELECT COUNT(*) AS total FROM {table}").fetchone()["total"],
            "columns": [row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()],
        }
    except sqlite3.Error as error:
        report[table] = {"error": str(error)}
career = connection.execute("SELECT manager.name AS manager_name, career.name AS career_name, career.current_club_id, team.nome AS club_name, team.estadio AS stadium_name FROM manager_careers career INNER JOIN managers manager ON manager.manager_id = career.manager_id LEFT JOIN times team ON team.time_id = career.current_club_id WHERE career.status='ACTIVE' ORDER BY career.updated_at DESC LIMIT 1").fetchone()
if career and career["current_club_id"] is not None:
    club_id = career["current_club_id"]
    report["active_career"] = dict(career)
    report["squad"] = {
        "total": connection.execute("SELECT COUNT(*) AS total FROM jogador_time WHERE time_id=?", (club_id,)).fetchone()["total"],
        "by_status": [dict(row) for row in connection.execute("SELECT status, COUNT(*) AS total FROM jogador_time WHERE time_id=? GROUP BY status ORDER BY status", (club_id,)).fetchall()],
        "sample": [dict(row) for row in connection.execute("SELECT player.jogador_id, player.nome, player.posicao, membership.status FROM jogador_time membership INNER JOIN jogadores player ON player.jogador_id=membership.jogador_id WHERE membership.time_id=? ORDER BY CASE membership.status WHEN 'Titular' THEN 0 ELSE 1 END, player.nome LIMIT 8", (club_id,)).fetchall()],
    }
    report["club_state"] = {
        "finance": dict(connection.execute("SELECT cash,updated_at FROM club_finances WHERE club_id=?", (club_id,)).fetchone() or {}),
        "reputation": dict(connection.execute("SELECT sporting,national,international,commercial,historical,updated_at FROM club_reputation WHERE club_id=?", (club_id,)).fetchone() or {}),
        "stadium": dict(connection.execute("SELECT name,capacity,usable_capacity,state,level,status FROM club_stadiums WHERE club_id=? AND is_primary=1", (club_id,)).fetchone() or {}),
    }
connection.close()
print(json.dumps(report, ensure_ascii=False, indent=2))
