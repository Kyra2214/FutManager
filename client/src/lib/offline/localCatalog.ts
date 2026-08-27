import { queryLocal } from "./localStore";
import type { OfflineAssetReference, OfflineEntityId } from "./contracts";

type ClubRow = {
  entityId: number;
  name: string;
  countryId: number | null;
  mappingStatus: string | null;
  assetPath: string | null;
};

type SelectionRow = {
  entityId: number;
  name: string;
  countryId: number | null;
  mappingStatus: string | null;
  assetPath: string | null;
};

function searchPattern(search: string) {
  return `%${search.trim()}%`;
}

export async function listLocalClubs(search = "", limit = 48) {
  const rows = await queryLocal<ClubRow>(
    `
      SELECT
        t.time_id AS entityId,
        t.nome AS name,
        t.pais_id AS countryId,
        l.mapping_status AS mappingStatus,
        a.relative_path AS assetPath
      FROM times t
      LEFT JOIN team_asset_links l ON l.time_id = t.time_id
      LEFT JOIN asset_catalog a ON a.asset_id = COALESCE(l.crest_asset_id, l.crest_mini_asset_id)
      WHERE TRIM(COALESCE(t.nome, '')) <> ''
        AND t.nome LIKE ? COLLATE NOCASE
      ORDER BY t.nome COLLATE NOCASE
      LIMIT ?
    `,
    [searchPattern(search), Math.max(1, Math.min(limit, 200))],
  );

  return rows.map((row) => ({
    entityId: row.entityId,
    name: row.name,
    countryId: row.countryId,
    mappingStatus: row.mappingStatus ?? "NO_SOURCE_ASSET",
    assetUrl: row.assetPath ? `/${row.assetPath}` : null,
    assetKind: row.assetPath ? "crest" as const : null,
  }));
}

export async function listLocalSelections(search = "", limit = 48) {
  const rows = await queryLocal<SelectionRow>(
    `
      SELECT
        s.selecao_id AS entityId,
        s.nome AS name,
        s.pais_id AS countryId,
        l.crest_status AS mappingStatus,
        a.relative_path AS assetPath
      FROM selecoes s
      LEFT JOIN selection_asset_links l ON l.selecao_id = s.selecao_id
      LEFT JOIN asset_catalog a ON a.asset_id = l.primary_kit_asset_id
      WHERE TRIM(COALESCE(s.nome, '')) <> ''
        AND s.nome LIKE ? COLLATE NOCASE
      ORDER BY s.nome COLLATE NOCASE
      LIMIT ?
    `,
    [searchPattern(search), Math.max(1, Math.min(limit, 200))],
  );

  return rows.map((row) => ({
    entityId: row.entityId,
    name: row.name,
    countryId: row.countryId,
    mappingStatus: row.mappingStatus ?? "SOURCE_NOT_PROVIDED",
    assetUrl: row.assetPath ? `/${row.assetPath}` : null,
    assetKind: row.assetPath ? "kit" as const : null,
  }));
}

export async function resolveLocalAsset(entityType: "team" | "selection", entityId: OfflineEntityId): Promise<OfflineAssetReference> {
  const key = entityType === "team" ? "team_asset_links" : "selection_asset_links";
  const idColumn = entityType === "team" ? "time_id" : "selecao_id";
  const assetColumn = entityType === "team" ? "COALESCE(crest_asset_id, crest_mini_asset_id)" : "primary_kit_asset_id";
  const rows = await queryLocal<{ assetPath: string | null }>(
    `SELECT a.relative_path AS assetPath FROM ${key} l LEFT JOIN asset_catalog a ON a.asset_id = ${assetColumn} WHERE l.${idColumn} = ? LIMIT 1`,
    [entityId],
  );
  const path = rows[0]?.assetPath ?? null;
  return { entityId, kind: entityType === "team" ? "club" : "selection", path: path ? `/${path}` : null };
}
