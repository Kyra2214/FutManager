import json
import sqlite3

db = sqlite3.connect("file:/home/ubuntu/brasfoot_engine/data/state/game.db?mode=ro", uri=True)
db.row_factory = sqlite3.Row
career = db.execute("SELECT current_club_id FROM manager_careers WHERE status='ACTIVE' ORDER BY updated_at DESC LIMIT 1").fetchone()
club_id = career["current_club_id"] if career else None
result = {"club_id": club_id}
if club_id is not None:
    result["club"] = dict(db.execute("SELECT team.time_id, team.nome, team.pais_id, country.nome AS pais FROM times team LEFT JOIN paises country ON country.pais_id = team.pais_id WHERE team.time_id=?", (club_id,)).fetchone())
    result["squad_power"] = dict(db.execute("""
        SELECT COUNT(*) AS players,
               AVG((player.cr1 + player.cr2) / 2.0) AS average_cr,
               AVG(CASE WHEN membership.status='Titular' THEN (player.cr1 + player.cr2) / 2.0 END) AS starter_average_cr,
               SUM(CASE WHEN player.estrela=1 THEN 1 ELSE 0 END) AS stars,
               SUM(CASE WHEN player.top_mundial=1 THEN 1 ELSE 0 END) AS world_class
        FROM jogador_time membership JOIN jogadores player ON player.jogador_id=membership.jogador_id
        WHERE membership.time_id=?
    """, (club_id,)).fetchone())
    result["staff"] = [dict(row) for row in db.execute("SELECT role, COUNT(*) AS count, AVG(level) AS average_level FROM staff_members WHERE club_id=? AND status='ativo' GROUP BY role", (club_id,))]
    result["departments"] = [dict(row) for row in db.execute("SELECT department, level, capacity, efficiency FROM club_departments WHERE club_id=?", (club_id,))]
result["clock"] = dict(db.execute("SELECT current_date,current_week,current_season FROM logical_clock WHERE clock_id=1").fetchone())
db.close()
print(json.dumps(result, ensure_ascii=False, indent=2))
