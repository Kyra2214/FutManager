import { afterEach, describe, expect, it } from "vitest";
import { createRequire } from "node:module";
import { mkdtempSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { getEntityAssetLink } from "./engineState";

type WritableSQLiteDatabase = { close: () => void; exec: (statement: string) => void };
type WritableSQLiteDatabaseConstructor = new (path: string) => WritableSQLiteDatabase;

const runtimeRequire = createRequire(import.meta.url);
const { DatabaseSync } = runtimeRequire(["node", "sqlite"].join(":")) as {
  DatabaseSync: WritableSQLiteDatabaseConstructor;
};

const temporaryFolders: string[] = [];

afterEach(() => {
  while (temporaryFolders.length) {
    const folder = temporaryFolders.pop();
    if (folder) rmSync(folder, { recursive: true, force: true });
  }
});

function createAssetFixture() {
  const directory = mkdtempSync(join(tmpdir(), "futmanager-assets-"));
  temporaryFolders.push(directory);
  const databasePath = join(directory, "game.db");
  const db = new DatabaseSync(databasePath);
  db.exec(`
    CREATE TABLE times (time_id INTEGER PRIMARY KEY, nome TEXT NOT NULL);
    CREATE TABLE selecoes (selecao_id INTEGER PRIMARY KEY, codigo TEXT NOT NULL, nome TEXT NOT NULL);
    CREATE TABLE asset_catalog (asset_id INTEGER PRIMARY KEY, relative_path TEXT NOT NULL);
    CREATE TABLE team_asset_links (time_id INTEGER PRIMARY KEY, mapping_status TEXT NOT NULL, crest_asset_id INTEGER, crest_mini_asset_id INTEGER);
    CREATE TABLE selection_asset_links (selecao_id INTEGER PRIMARY KEY, crest_status TEXT NOT NULL, crest_asset_id INTEGER, primary_kit_asset_id INTEGER);
    INSERT INTO times VALUES (7, 'Clube Exemplo');
    INSERT INTO selecoes VALUES (4, 'ARG', 'Argentina');
    INSERT INTO asset_catalog VALUES (11, 'assets/escudos/clubes/exemplo.png'), (12, 'assets/escudos/clubes_mini/exemplo.png'), (13, 'assets/selecoes/camisas/ARG.png');
    INSERT INTO team_asset_links VALUES (7, 'COMPLETE', 11, 12);
    INSERT INTO selection_asset_links VALUES (4, 'SOURCE_NOT_PROVIDED', NULL, 13);
  `);
  db.close();
  return databasePath;
}

describe("getEntityAssetLink", () => {
  it("resolve o escudo de um clube pelo ID e expõe URL estática segura", () => {
    const asset = getEntityAssetLink("team", 7, createAssetFixture());

    expect(asset).toMatchObject({
      entityName: "Clube Exemplo",
      mappingStatus: "COMPLETE",
      crestUrl: "/engine-assets/escudos/clubes/exemplo.png",
      miniCrestUrl: "/engine-assets/escudos/clubes_mini/exemplo.png",
    });
  });

  it("mantém a ausência de escudo de seleção explícita e entrega somente a camisa fonte", () => {
    const asset = getEntityAssetLink("selection", 4, createAssetFixture());

    expect(asset).toMatchObject({
      entityName: "Argentina",
      mappingStatus: "SOURCE_NOT_PROVIDED",
      crestUrl: null,
      primaryKitUrl: "/engine-assets/selecoes/camisas/ARG.png",
    });
  });
});
