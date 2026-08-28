import { afterEach, describe, expect, it } from "vitest";
import { copyFileSync, mkdtempSync, rmSync } from "node:fs";
import { createRequire } from "node:module";
import { join, resolve } from "node:path";
import { tmpdir } from "node:os";
import { appRouter } from "./routers";

const ENGINE_ROOT = process.env.FUTMANAGER_ENGINE_ROOT || resolve(import.meta.dirname, "../../engine");
const ENGINE_STATE = process.env.FUTMANAGER_ENGINE_STATE_PATH || join(ENGINE_ROOT, "data/state/game.db");
const folders: string[] = [];
const originalStatePath = process.env.FUTMANAGER_ENGINE_STATE_PATH;
type WritableDb = { close: () => void; exec: (sql: string) => void };
type WritableDbConstructor = new (path: string) => WritableDb;
const runtimeRequire = createRequire(import.meta.url);
const { DatabaseSync } = runtimeRequire(["node", "sqlite"].join(":")) as { DatabaseSync: WritableDbConstructor };

afterEach(() => {
  if (originalStatePath === undefined) delete process.env.FUTMANAGER_ENGINE_STATE_PATH;
  else process.env.FUTMANAGER_ENGINE_STATE_PATH = originalStatePath;
  while (folders.length) {
    const folder = folders.pop();
    if (folder) rmSync(folder, { recursive: true, force: true });
  }
});

describe("careerRouter integration", () => {
  it("cria uma carreira usando o contrato tRPC e o gateway real em banco temporário", async () => {
    const folder = mkdtempSync(join(tmpdir(), "futmanager-career-router-"));
    folders.push(folder);
    const databasePath = join(folder, "game.db");
    copyFileSync(ENGINE_STATE, databasePath);
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

    const weekly = await caller.career.advanceWeek({ seed: 11 });
    expect(weekly).toMatchObject({ status: "COMPLETED", week: expect.any(Number), season: expect.any(Number), controlled_club_id: 2009 });
    expect((weekly as { skipped_controlled_matches: number }).skipped_controlled_matches).toBeGreaterThanOrEqual(0);
  });
});
