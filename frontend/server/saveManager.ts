import { copyFileSync, existsSync, mkdirSync, readFileSync, renameSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { DatabaseSync } from "node:sqlite";

const MODULE_ROOT = dirname(fileURLToPath(import.meta.url));
const ENGINE_ROOT = process.env.FUTMANAGER_ENGINE_ROOT || resolve(MODULE_ROOT, "../../engine");
const DEFAULT_DATABASE_PATH = resolve(ENGINE_ROOT, "data/state/game.db");
const CANONICAL_DATABASE_PATH = resolve(ENGINE_ROOT, "data/database/game.db");
const SAVE_ROOT = resolve(ENGINE_ROOT, "data/state/saves");
const INDEX_PATH = join(SAVE_ROOT, "index.json");
export const SAVE_SLOT_COOKIE = "futmanager_save_slot";
export const DEFAULT_SAVE_SLOT = "default";
const MAX_SLOTS = 10;

type SaveMeta = { id: string; name: string; createdAt: string; updatedAt: string };

function ensureRoot() { mkdirSync(SAVE_ROOT, { recursive: true }); }
function validId(id: string) { return /^[a-z0-9][a-z0-9_-]{0,31}$/i.test(id) && id !== "default"; }
function readIndex(): SaveMeta[] {
  ensureRoot();
  if (!existsSync(INDEX_PATH)) return [];
  try {
    const parsed = JSON.parse(readFileSync(INDEX_PATH, "utf8"));
    return Array.isArray(parsed) ? parsed.filter((item): item is SaveMeta => !!item && typeof item.id === "string" && validId(item.id)) : [];
  } catch { return []; }
}
function writeIndex(items: SaveMeta[]) {
  ensureRoot(); const temp = `${INDEX_PATH}.tmp`; writeFileSync(temp, JSON.stringify(items, null, 2), "utf8"); renameSync(temp, INDEX_PATH);
}
function slotPath(id: string) {
  if (id === DEFAULT_SAVE_SLOT) return DEFAULT_DATABASE_PATH;
  if (!validId(id)) throw new Error("SAVE_SLOT_INVALID");
  return join(SAVE_ROOT, `${id}.db`);
}
function now() { return new Date().toISOString(); }
function careerSummary(databasePath: string) {
  if (!existsSync(databasePath)) return null;
  try {
    const db = new DatabaseSync(databasePath, { readOnly: true });
    try {
      const row = db.prepare(`SELECT career_id, name, current_club_id, status, updated_at FROM manager_careers ORDER BY updated_at DESC, career_id DESC LIMIT 1`).get() as Record<string, unknown> | undefined;
      return row ? { careerId: Number(row.career_id), name: String(row.name), currentClubId: row.current_club_id == null ? null : Number(row.current_club_id), status: String(row.status), updatedAt: String(row.updated_at) } : null;
    } finally { db.close(); }
  } catch { return null; }
}
export function listSaveSlots() {
  const items = readIndex();
  return [{ id: DEFAULT_SAVE_SLOT, name: "Jogo principal", createdAt: null, updatedAt: null, databasePath: DEFAULT_DATABASE_PATH, career: careerSummary(DEFAULT_DATABASE_PATH), isDefault: true }, ...items.map(item => ({ ...item, databasePath: slotPath(item.id), career: careerSummary(slotPath(item.id)), isDefault: false }))];
}
export function resolveSaveDatabasePath(id: string | undefined | null) {
  const slot = id || DEFAULT_SAVE_SLOT;
  if (slot !== DEFAULT_SAVE_SLOT && !readIndex().some(item => item.id === slot)) throw new Error("SAVE_SLOT_NOT_FOUND");
  return slotPath(slot);
}
export function createSaveSlot(name: string, sourceSlot = DEFAULT_SAVE_SLOT) {
  const cleanName = name.trim();
  if (!cleanName || cleanName.length > 40) throw new Error("SAVE_NAME_INVALID");
  const items = readIndex(); if (items.length >= MAX_SLOTS) throw new Error("SAVE_SLOT_LIMIT_REACHED");
  const baseId = cleanName.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 24) || "save";
  let id = baseId; let suffix = 2; while (items.some(item => item.id === id) || id === DEFAULT_SAVE_SLOT) id = `${baseId}-${suffix++}`;
  const requestedSource = resolveSaveDatabasePath(sourceSlot);
  const sourcePath = existsSync(requestedSource) ? requestedSource : CANONICAL_DATABASE_PATH;
  if (!existsSync(sourcePath)) throw new Error("SAVE_SOURCE_DATABASE_NOT_FOUND");
  const targetPath = slotPath(id); ensureRoot(); copyFileSync(sourcePath, targetPath);
  const timestamp = now(); const meta: SaveMeta = { id, name: cleanName, createdAt: timestamp, updatedAt: timestamp };
  writeIndex([...items, meta]); return { ...meta, databasePath: targetPath, career: careerSummary(targetPath), isDefault: false };
}
export function deleteSaveSlot(id: string) {
  if (id === DEFAULT_SAVE_SLOT) throw new Error("DEFAULT_SAVE_CANNOT_DELETE");
  const items = readIndex(); if (!items.some(item => item.id === id)) throw new Error("SAVE_SLOT_NOT_FOUND");
  const path = slotPath(id); if (existsSync(path)) rmSync(path, { force: true }); writeIndex(items.filter(item => item.id !== id)); return { success: true, id };
}
export function renameSaveSlot(id: string, name: string) {
  if (id === DEFAULT_SAVE_SLOT) throw new Error("DEFAULT_SAVE_CANNOT_RENAME");
  const cleanName = name.trim(); if (!cleanName || cleanName.length > 40) throw new Error("SAVE_NAME_INVALID");
  const items = readIndex(); const index = items.findIndex(item => item.id === id); if (index < 0) throw new Error("SAVE_SLOT_NOT_FOUND");
  items[index] = { ...items[index], name: cleanName, updatedAt: now() }; writeIndex(items); return items[index];
}
export function touchSaveSlot(id: string) {
  if (id === DEFAULT_SAVE_SLOT) return; const items = readIndex(); const index = items.findIndex(item => item.id === id); if (index < 0) return;
  items[index] = { ...items[index], updatedAt: now() }; writeIndex(items);
}
