import { TRPCError } from "@trpc/server";
import { z } from "zod";
import { bootstrapClubEconomy, getClubEconomySummary, hireAvailableStaff, listAvailableStaff, listDepartmentOffers, upgradeClubDepartment } from "../careerGateway";
import { publicProcedure, router } from "../_core/trpc";

function toTrpcError(error: unknown) {
  const message = error instanceof Error ? error.message : "STAFF_MARKET_ACTION_FAILED";
  const code = message === "INSUFFICIENT_CASH" ? "PRECONDITION_FAILED" : message.endsWith("NOT_FOUND") ? "NOT_FOUND" : message.endsWith("UNAVAILABLE") ? "CONFLICT" : "BAD_REQUEST";
  return new TRPCError({ code, message });
}

export const staffMarketRouter = router({
  bootstrap: publicProcedure.mutation(() => {
    try { return bootstrapClubEconomy(); } catch (error) { throw toTrpcError(error); }
  }),
  summary: publicProcedure.query(() => {
    try { return getClubEconomySummary(); } catch (error) { throw toTrpcError(error); }
  }),
  catalog: publicProcedure.input(z.object({ role: z.enum(["treinador", "auxiliar", "preparador_fisico", "medico", "scout"]).optional() }).default({})).query(({ input }) => {
    try { return listAvailableStaff(input.role); } catch (error) { throw toTrpcError(error); }
  }),
  hire: publicProcedure.input(z.object({ staffId: z.number().int().positive() })).mutation(({ input }) => {
    try { return hireAvailableStaff(input.staffId); } catch (error) { throw toTrpcError(error); }
  }),
  departmentOffers: publicProcedure.query(() => {
    try { return listDepartmentOffers(); } catch (error) { throw toTrpcError(error); }
  }),
  upgradeDepartment: publicProcedure.input(z.object({ department: z.enum(["base", "medicina", "preparacao_fisica", "analise"]) })).mutation(({ input }) => {
    try { return upgradeClubDepartment(input.department); } catch (error) { throw toTrpcError(error); }
  }),
});
