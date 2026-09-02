import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { DatabaseSync } from "node:sqlite";

const MODULE_ROOT = dirname(fileURLToPath(import.meta.url));
const ENGINE_ROOT = process.env.FUTMANAGER_ENGINE_ROOT || resolve(MODULE_ROOT, "../../engine");
const DEFAULT_ENGINE_STATE_PATH = resolve(ENGINE_ROOT, "data/state/game.db");

function tableExists(db: DatabaseSync, table: string) {
  return Boolean(db.prepare("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?").get(table));
}

export function getCurrentCareerReadOnly(databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH) {
  const db = new DatabaseSync(databasePath, { readOnly: true });
  try {
    if (!tableExists(db, "manager_careers")) return { ok: true, started: false };

    const row = db.prepare(`
      SELECT career.career_id,
             career.name AS career_name,
             career.status,
             career.current_club_id,
             manager.name AS manager_name,
             manager.nationality,
             manager.age
      FROM manager_careers career
      INNER JOIN managers manager ON manager.manager_id = career.manager_id
      WHERE career.status='ACTIVE'
      ORDER BY career.updated_at DESC, career.career_id DESC
      LIMIT 1
    `).get() as Record<string, unknown> | undefined;

    if (!row) return { ok: true, started: false };

    const clubId = row.current_club_id == null ? null : Number(row.current_club_id);
    let targetName: string | undefined;
    let targetType: "club" | "selection" | undefined;

    if (clubId != null && tableExists(db, "times")) {
      const club = db.prepare("SELECT nome FROM times WHERE time_id=?").get(clubId) as { nome?: string } | undefined;
      if (club?.nome) {
        targetName = club.nome;
        targetType = "club";
      }
    }

    if (tableExists(db, "manager_selection_assignments") && tableExists(db, "selecoes")) {
      const selection = db.prepare(`
        SELECT selection.selecao_id, selection.nome
        FROM manager_selection_assignments assignment
        INNER JOIN selecoes selection ON selection.selecao_id=assignment.selection_id
        WHERE assignment.career_id=? AND assignment.status='ACTIVE'
        ORDER BY assignment.selecao_id
        LIMIT 1
      `).get(Number(row.career_id)) as { selecao_id?: number; nome?: string } | undefined;
      if (selection?.selecao_id != null) {
        targetName = selection.nome || targetName;
        targetType = "selection";
      }
    }

    return {
      ok: true,
      started: true,
      careerId: Number(row.career_id),
      careerName: String(row.career_name || "Carreira"),
      managerName: String(row.manager_name || "Manager"),
      nationality: row.nationality == null ? null : String(row.nationality),
      age: row.age == null ? null : Number(row.age),
      targetId: clubId,
      targetName,
      targetType,
    };
  } finally {
    db.close();
  }
}
