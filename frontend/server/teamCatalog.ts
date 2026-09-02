import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { DatabaseSync } from "node:sqlite";

const MODULE_ROOT = dirname(fileURLToPath(import.meta.url));
const ENGINE_ROOT = process.env.FUTMANAGER_ENGINE_ROOT || resolve(MODULE_ROOT, "../../engine");
const DEFAULT_ENGINE_STATE_PATH = resolve(ENGINE_ROOT, "data/state/game.db");

export type TeamCatalogItem = {
  entityId: number;
  name: string;
  countryId: number | null;
  mappingStatus: string;
  assetUrl: string | null;
  assetKind: "crest" | "kit" | null;
};

function normalize(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR")
    .trim();
}

function assetUrl(relativePath: string | null) {
  if (!relativePath || !relativePath.startsWith("assets/") || relativePath.includes("..")) return null;
  return `/engine-assets/${relativePath.slice("assets/".length).split("/").join("/")}`;
}

export function listTeamCatalog(search = "", limit = 48, databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH): TeamCatalogItem[] {
  const db = new DatabaseSync(databasePath, { readOnly: true });
  try {
    const rows = db.prepare(`
      SELECT team.time_id AS entity_id,
             team.nome AS entity_name,
             team.arquivo_origem AS source_file,
             team.pais_id AS country_id,
             COALESCE(link.mapping_status, 'NO_SOURCE_ASSET') AS mapping_status,
             crest.relative_path AS crest_path,
             mini.relative_path AS mini_crest_path
      FROM times team
      LEFT JOIN team_asset_links link ON link.time_id = team.time_id
      LEFT JOIN asset_catalog crest ON crest.asset_id = link.crest_asset_id
      LEFT JOIN asset_catalog mini ON mini.asset_id = link.crest_mini_asset_id
      WHERE trim(COALESCE(team.nome, '')) <> ''
        AND lower(trim(team.nome)) NOT LIKE 'sem contrato%'
      ORDER BY team.nome COLLATE NOCASE, team.time_id
    `).all() as Array<Record<string, unknown>>;

    const needle = normalize(search);
    return rows
      .filter((row) => {
        if (!needle) return true;
        return normalize(String(row.entity_name ?? "")).includes(needle)
          || normalize(String(row.source_file ?? "")).includes(needle);
      })
      .slice(0, Math.min(Math.max(limit, 1), 96))
      .map((row) => {
        const relativePath = String(row.crest_path ?? row.mini_crest_path ?? "") || null;
        return {
          entityId: Number(row.entity_id),
          name: String(row.entity_name),
          countryId: row.country_id == null ? null : Number(row.country_id),
          mappingStatus: String(row.mapping_status),
          assetUrl: assetUrl(relativePath),
          assetKind: relativePath ? "crest" : null,
        };
      });
  } finally {
    db.close();
  }
}
