import { Capacitor } from "@capacitor/core";
import { queryLocal } from "./localStore";
import { NativeEngine } from "./nativeEngine";
import type { OfflineAssetReference, OfflineEntityId } from "./contracts";

export type OfflineCountry = {
  countryId: number;
  name: string;
  code: string | null;
  clubCount: number;
  firstDivisionClubCount: number;
  firstDivisionName: string | null;
  supported: boolean;
};

let offlineCountriesPromise: Promise<OfflineCountry[]> | undefined;

export function loadLocalCountries(search = "") {
  offlineCountriesPromise ??= Capacitor.isNativePlatform()
    ? NativeEngine.readDataFile({ path: "offline-countries.json" }).then(({ content }) => JSON.parse(content) as OfflineCountry[])
    : fetch("/assets/offline-countries.json").then((response) => {
      if (!response.ok) throw new Error("Catálogo de países offline indisponível.");
      return response.json() as Promise<OfflineCountry[]>;
    });
  const normalized = search.trim().toLocaleLowerCase();
  return offlineCountriesPromise.then((countries) => normalized
    ? countries.filter((country) => `${country.name} ${country.code ?? ""}`.toLocaleLowerCase().includes(normalized))
    : countries);
}

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

async function resolveAssetUrl(assetPath: string | null) {
  if (!assetPath) return null;
  if (!Capacitor.isNativePlatform()) return `/${assetPath}`;
  const { uri } = await NativeEngine.getDataAssetUrl({ path: assetPath });
  return Capacitor.convertFileSrc(uri);
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

  return Promise.all(rows.map(async (row) => ({
    entityId: row.entityId,
    name: row.name,
    countryId: row.countryId,
    mappingStatus: row.mappingStatus ?? "NO_SOURCE_ASSET",
    assetUrl: await resolveAssetUrl(row.assetPath),
    assetKind: row.assetPath ? "crest" as const : null,
  })));
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

  return Promise.all(rows.map(async (row) => ({
    entityId: row.entityId,
    name: row.name,
    countryId: row.countryId,
    mappingStatus: row.mappingStatus ?? "SOURCE_NOT_PROVIDED",
    assetUrl: await resolveAssetUrl(row.assetPath),
    assetKind: row.assetPath ? "kit" as const : null,
  })));
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
  return { entityId, kind: entityType === "team" ? "club" : "selection", path: path ? await resolveAssetUrl(path) : null };
}
