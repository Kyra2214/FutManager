import { afterEach, describe, expect, it } from "vitest";
import { copyFileSync, mkdtempSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { appRouter } from "./routers";

const ENGINE_STATE = "/home/ubuntu/brasfoot_engine/data/state/game.db";
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
  it("cria uma carreira usando o contrato tRPC e o gateway real em banco temporário", async () => {
    const folder = mkdtempSync(join(tmpdir(), "futmanager-career-router-"));
    folders.push(folder);
    const databasePath = join(folder, "game.db");
    copyFileSync(ENGINE_STATE, databasePath);
    process.env.FUTMANAGER_ENGINE_STATE_PATH = databasePath;

    const caller = appRouter.createCaller({} as never);
    const catalog = await caller.career.catalog({ targetType: "club", search: "07 Vestur", limit: 4 });
    expect(catalog[0]).toMatchObject({ entityId: 1, name: "07 Vestur" });
    expect(await caller.career.current()).toMatchObject({ started: false });

    const started = await caller.career.start({ managerName: "Manager Router", nationality: "BR", age: 30, careerName: "Integração", targetType: "club", targetId: 1 });
    expect(started).toMatchObject({ started: true, target_id: 1 });
    expect(await caller.career.current()).toMatchObject({ started: true, managerName: "Manager Router", targetType: "club", targetId: 1, targetName: "07 Vestur" });
  });
});
