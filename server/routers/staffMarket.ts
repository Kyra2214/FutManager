import { TRPCError } from "@trpc/server";
import { z } from "zod";
import { bootstrapClubEconomy, getClubEconomySummary, getStaffContract, hireAvailableStaff, listAvailableStaff, listDepartmentOffers, replaceStaff, terminateStaff, upgradeClubDepartment } from "../careerGateway";
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
  catalog: publicProcedure.input(z.object({ role: z.enum(["treinador", "auxiliar", "preparador_fisico", "medico", "scout"]).optional(), minLevel: z.number().int().min(1).max(10).optional(), maxLevel: z.number().int().min(1).max(10).optional() }).default({})).query(({ input }) => {
    try { return listAvailableStaff(input.role, input.minLevel, input.maxLevel); } catch (error) { throw toTrpcError(error); }
  }),
  hire: publicProcedure.input(z.object({ staffId: z.number().int().positive() })).mutation(({ input }) => {
    try { return hireAvailableStaff(input.staffId); } catch (error) { throw toTrpcError(error); }
  }),
  contract: publicProcedure.input(z.object({ staffId: z.number().int().positive() })).query(({ input }) => {
    try { return getStaffContract(input.staffId); } catch (error) { throw toTrpcError(error); }
  }),
  terminate: publicProcedure.input(z.object({ staffId: z.number().int().positive(), waiveFee: z.boolean().optional() })).mutation(({ input }) => {
    try { return terminateStaff(input.staffId, input.waiveFee ?? false); } catch (error) { throw toTrpcError(error); }
  }),
  replace: publicProcedure.input(z.object({ outgoingStaffId: z.number().int().positive(), incomingStaffId: z.number().int().positive() })).mutation(({ input }) => {
    try { return replaceStaff(input.outgoingStaffId, input.incomingStaffId); } catch (error) { throw toTrpcError(error); }
  }),
  departmentOffers: publicProcedure.query(() => {
    try { return listDepartmentOffers(); } catch (error) { throw toTrpcError(error); }
  }),
  upgradeDepartment: publicProcedure.input(z.object({ department: z.enum(["base", "medicina", "preparacao_fisica", "analise"]) })).mutation(({ input }) => {
    try { return upgradeClubDepartment(input.department); } catch (error) { throw toTrpcError(error); }
  }),
});
