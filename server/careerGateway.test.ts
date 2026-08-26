import { afterEach, describe, expect, it } from "vitest";
import { createRequire } from "node:module";
import { mkdtempSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { getCurrentCareer, listCareerTargets, startCareer } from "./careerGateway";

type Db = { close: () => void; exec: (sql: string) => void };
type DbConstructor = new (path: string) => Db;
const runtimeRequire = createRequire(import.meta.url);
const { DatabaseSync } = runtimeRequire(["node", "sqlite"].join(":")) as { DatabaseSync: DbConstructor };
const folders: string[] = [];

afterEach(() => {
  while (folders.length) {
    const folder = folders.pop();
    if (folder) rmSync(folder, { recursive: true, force: true });
  }
});

function fixture() {
  const folder = mkdtempSync(join(tmpdir(), "futmanager-career-"));
  folders.push(folder);
  const path = join(folder, "game.db");
  const db = new DatabaseSync(path);
  db.exec(`
    CREATE TABLE times(time_id INTEGER PRIMARY KEY, arquivo_origem TEXT, nome TEXT NOT NULL);
    CREATE TABLE selecoes(selecao_id INTEGER PRIMARY KEY, codigo TEXT, nome TEXT NOT NULL);
    CREATE TABLE asset_catalog(asset_id INTEGER PRIMARY KEY, relative_path TEXT NOT NULL);
    CREATE TABLE team_asset_links(time_id INTEGER PRIMARY KEY, mapping_status TEXT NOT NULL, crest_asset_id INTEGER, crest_mini_asset_id INTEGER);
    CREATE TABLE selection_asset_links(selecao_id INTEGER PRIMARY KEY, crest_status TEXT NOT NULL, crest_asset_id INTEGER, primary_kit_asset_id INTEGER);
    INSERT INTO times VALUES(7,'clube_exemplo.ban','Clube Exemplo');
    INSERT INTO selecoes VALUES(4,'ARG','Argentina');
    INSERT INTO asset_catalog VALUES(1,'assets/escudos/clubes/exemplo.png'),(2,'assets/selecoes/camisas/ARG.png');
    INSERT INTO team_asset_links VALUES(7,'COMPLETE',1,NULL);
    INSERT INTO selection_asset_links VALUES(4,'SOURCE_NOT_PROVIDED',NULL,2);
  `);
  db.close();
  return path;
}

describe("careerGateway", () => {
  it("lista os destinos oficiais e inicia uma carreira sem criar estado paralelo", () => {
    const path = fixture();
    expect(getCurrentCareer(path)).toMatchObject({ started: false });
    expect(listCareerTargets("club", "Exemplo", 8, path)[0]).toMatchObject({ entityId: 7, assetUrl: "/engine-assets/escudos/clubes/exemplo.png" });
    expect(listCareerTargets("selection", "ARG", 8, path)[0]).toMatchObject({ entityId: 4, assetKind: "kit" });
    expect(startCareer({ managerName: "Ana", nationality: "BR", age: 31, careerName: "Carreira Ana", targetType: "club", targetId: 7 }, path)).toMatchObject({ started: true, target_id: 7 });
    expect(getCurrentCareer(path)).toMatchObject({ started: true, targetType: "club", targetId: 7, managerName: "Ana" });
    expect(() => startCareer({ managerName: "Bia", age: 29, careerName: "Outra", targetType: "club", targetId: 7 }, path)).toThrow("ACTIVE_CAREER_EXISTS");
  });

  it("recusa uma entidade inexistente sem criar manager", () => {
    const path = fixture();
    expect(() => startCareer({ managerName: "Bia", age: 29, careerName: "Outra", targetType: "club", targetId: 999 }, path)).toThrow("CLUB_NOT_FOUND");
    expect(getCurrentCareer(path)).toMatchObject({ started: false });
  });
});
