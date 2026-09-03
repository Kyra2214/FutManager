import { afterEach, describe, expect, it } from "vitest";
import { copyFileSync, existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { DatabaseSync } from "node:sqlite";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { appRouter } from "./routers";

const ENGINE_STATE = process.env.FUTMANAGER_ENGINE_STATE_PATH;
const DEFAULT_ENGINE_STATE = join(process.cwd(), "../engine/data/state/game.db");
const ENGINE_STATE_GZ = process.env.FUTMANAGER_ENGINE_STATE_GZ || join(process.cwd(), "../engine/data/state/game.db.gz");
const folders: string[] = [];
const originalStatePath = process.env.FUTMANAGER_ENGINE_STATE_PATH;

afterEach(() => {
  if (originalStatePath === undefined) delete process.env.FUTMANAGER_ENGINE_STATE_PATH;
  else process.env.FUTMANAGER_ENGINE_STATE_PATH = originalStatePath;
  while (folders.length) {
    const folder = folders.pop();
    if (folder) rmSync(folder, { recursive: true, force: true });
  }
});

describe("careerRouter integration", () => {
  it.skipIf(!ENGINE_STATE && !existsSync(ENGINE_STATE_GZ) && !existsSync(DEFAULT_ENGINE_STATE))("cria uma carreira usando o contrato tRPC e o gateway real em banco temporário", async () => {
    const folder = mkdtempSync(join(tmpdir(), "futmanager-career-router-"));
    folders.push(folder);
    const databasePath = join(folder, "game.db");
    if (ENGINE_STATE) copyFileSync(ENGINE_STATE, databasePath);
    else if (existsSync(ENGINE_STATE_GZ)) writeFileSync(databasePath, gunzipSync(readFileSync(ENGINE_STATE_GZ)));
    else copyFileSync(DEFAULT_ENGINE_STATE, databasePath);
    const isolatedDb = new DatabaseSync(databasePath);
    isolatedDb.exec("DELETE FROM manager_selection_assignments; DELETE FROM manager_careers; DELETE FROM managers;");
    isolatedDb.close();
    process.env.FUTMANAGER_ENGINE_STATE_PATH = databasePath;

    const caller = appRouter.createCaller({} as never);
    const catalog = await caller.career.catalog({ targetType: "club", search: "07 Vestur", limit: 4 });
    expect(catalog[0]).toMatchObject({ entityId: 1, name: "07 Vestur", countryId: 92 });
    const countries = await caller.career.worldCountries({ search: "", limit: 96 });
    expect(countries.items).toContainEqual(expect.objectContaining({ countryId: 29, name: "Brasil" }));
    expect(await caller.career.current()).toMatchObject({ started: false });

    const started = await caller.career.start({ managerName: "Manager Router", nationality: "BR", age: 30, careerName: "Integração", targetType: "club", targetId: 2009, selectedCountryIds: [29, 104, 65, 154] });
    expect(started).toMatchObject({ started: true, target_id: 2009, starting_division: 4, selected_country_ids: [29, 104, 65, 154], parallel_league: { total_clubs: 80, division_count: 4, target_division: 4 } });
    expect(await caller.career.current()).toMatchObject({ started: true, managerName: "Manager Router", targetType: "club", targetId: 2009, targetName: "RB Bragantino", startingDivision: 4, selectedCountryIds: [29, 65, 104, 154], combinedLeagueName: "Brasil + Itália + Espanha + Portugal", parallelLeague: { totalClubs: 80, divisionCount: 4 } });

    // A simulação de semana completa executa o motor Python real e já possui cobertura
    // própria no job do engine. Mantemos este teste focado no contrato tRPC, isolamento
    // do banco temporário e ciclo de criação/consulta da carreira, evitando duplicar uma
    // simulação pesada dentro da suíte frontend.
  });
});
