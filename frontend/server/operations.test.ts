import { describe, expect, it } from "vitest";
import { appRouter } from "./routers";
import type { TrpcContext } from "./_core/context";

function unauthenticatedContext(): TrpcContext {
  return {
    user: null,
    req: { protocol: "https", headers: {} } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

describe("operations router", () => {
  it("protege snapshots, simulação e auditoria financeira por autenticação", async () => {
    const caller = appRouter.createCaller(unauthenticatedContext());
    await expect(caller.operations.snapshots.audit()).rejects.toMatchObject({ code: "UNAUTHORIZED" });
    await expect(caller.operations.simulation.progress({ tickId: "season-2027-week-01" })).rejects.toMatchObject({ code: "UNAUTHORIZED" });
    await expect(caller.operations.finance.monthlyClose({ season: 2027, month: 1 })).rejects.toMatchObject({ code: "UNAUTHORIZED" });
  });

  it("mantém autorização como primeira barreira mesmo com payload inválido", async () => {
    const caller = appRouter.createCaller(unauthenticatedContext());
    await expect(caller.operations.simulation.progress({ tickId: "" })).rejects.toMatchObject({ code: "UNAUTHORIZED" });
  });
});
