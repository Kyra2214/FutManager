import { DatabaseSync } from "node:sqlite";
import { resolve } from "node:path";
import { runAiWeekly } from "./careerGateway";

const DEFAULT_ENGINE_STATE_PATH = resolve(process.cwd(), "../engine/data/state/game.db");

function databasePath() {
  return process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH;
}

function logicalClock() {
  const db = new DatabaseSync(databasePath(), { readOnly: true });
  try {
    const row = db.prepare("SELECT current_season, current_week FROM logical_clock WHERE clock_id=1").get() as Record<string, unknown> | undefined;
    return row ? { season: Number(row.current_season), week: Number(row.current_week) } : { season: 2026, week: 1 };
  } finally { db.close(); }
}

function currentClubId() {
  const db = new DatabaseSync(databasePath(), { readOnly: true });
  try {
    const row = db.prepare("SELECT current_club_id FROM manager_careers WHERE status='ACTIVE' ORDER BY updated_at DESC, career_id DESC LIMIT 1").get() as Record<string, unknown> | undefined;
    return row?.current_club_id == null ? null : Number(row.current_club_id);
  } finally { db.close(); }
}

function repairTransferWindowDecision(clubId: number | null, seed: number | undefined, season: number, week: number) {
  if (clubId == null) return;
  const db = new DatabaseSync(databasePath());
  try {
    const row = db.prepare(`SELECT decision_id FROM club_decision_history WHERE club_id=? AND type='TRANSFER_WINDOW' AND seed IS ? ORDER BY decision_id DESC LIMIT 1`).get(clubId, seed ?? null) as Record<string, unknown> | undefined;
    if (!row) return;
    db.prepare("UPDATE club_decision_history SET target=? WHERE decision_id=?").run(`${season}:${week}`, Number(row.decision_id));
  } finally { db.close(); }
}

export function runAiWeeklyWithLogicalClock(seed?: number) {
  const clock = logicalClock();
  const clubId = currentClubId();
  const result = runAiWeekly(seed);
  repairTransferWindowDecision(clubId, seed, clock.season, clock.week);
  return { ...result, logicalClock: clock };
}
