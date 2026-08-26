import { TRPCError } from "@trpc/server";
import { z } from "zod";
import { approveTransferOffer, bootstrapClubEconomy, createTrainingPlan, createTransferLoan, createTransferOffer, getAiDiagnosis, getAiHistory, getAiLineup, getAiTactic, getClubEconomySummary, getFormRecommendations, getMoraleSummary, getStaffContract, getWeeklyLoad, hireAvailableStaff, listAvailableStaff, listDepartmentOffers, listHealth, listHealthAlerts, listTrainingAlerts, listTrainingBudget, listTrainingDepartments, listTrainingDevelopment, listTransferablePlayers, recoverPlayers, registerInjury, registerSuspension, replaceStaff, runAiWeekly, terminateStaff, upgradeClubDepartment } from "../careerGateway";
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
  trainingDepartments: publicProcedure.query(() => { try { return listTrainingDepartments(); } catch (error) { throw toTrpcError(error); } }),
  trainingBudget: publicProcedure.query(() => { try { return listTrainingBudget(); } catch (error) { throw toTrpcError(error); } }),
  trainingDevelopment: publicProcedure.query(() => { try { return listTrainingDevelopment(); } catch (error) { throw toTrpcError(error); } }),
  trainingAlerts: publicProcedure.query(() => { try { return listTrainingAlerts(); } catch (error) { throw toTrpcError(error); } }),
  trainingPlan: publicProcedure.input(z.object({ season: z.number().int().positive(), week: z.number().int().min(1).max(53), planType: z.enum(["GENERAL", "TECHNICAL", "TACTICAL", "PHYSICAL", "SET_PIECES", "REST"]), load: z.number().int().min(0).max(100) })).mutation(({ input }) => { try { return createTrainingPlan(input.season, input.week, input.planType, input.load); } catch (error) { throw toTrpcError(error); } }),
  aiDiagnosis: publicProcedure.query(() => { try { return getAiDiagnosis(); } catch (error) { throw toTrpcError(error); } }),
  aiHistory: publicProcedure.query(() => { try { return getAiHistory(); } catch (error) { throw toTrpcError(error); } }),
  aiWeekly: publicProcedure.input(z.object({ seed: z.number().int().optional() }).optional()).mutation(({ input }) => { try { return runAiWeekly(input?.seed); } catch (error) { throw toTrpcError(error); } }),
  aiLineup: publicProcedure.input(z.object({ seed: z.number().int().optional() }).optional()).mutation(({ input }) => { try { return getAiLineup(input?.seed); } catch (error) { throw toTrpcError(error); } }),
  aiTactic: publicProcedure.input(z.object({ seed: z.number().int().optional() }).optional()).mutation(({ input }) => { try { return getAiTactic(input?.seed); } catch (error) { throw toTrpcError(error); } }),
  transferables: publicProcedure.query(() => { try { return listTransferablePlayers(); } catch (error) { throw toTrpcError(error); } }),
  transferOffer: publicProcedure.input(z.object({ playerId: z.number().int().positive(), sellerClubId: z.number().int().positive(), value: z.number().int().nonnegative(), windowId: z.number().int().positive(), askingPrice: z.number().int().nonnegative().optional(), validUntil: z.string().optional(), salary: z.number().int().nonnegative().optional(), commission: z.number().int().nonnegative().optional(), accessoryCost: z.number().int().nonnegative().optional() })).mutation(({ input }) => { try { return createTransferOffer({ player_id: input.playerId, seller_club_id: input.sellerClubId, value: input.value, window_id: input.windowId, asking_price: input.askingPrice, valid_until: input.validUntil, salary: input.salary ?? 0, commission: input.commission ?? 0, accessory_cost: input.accessoryCost ?? 0 }); } catch (error) { throw toTrpcError(error); } }),
  transferApprove: publicProcedure.input(z.object({ offerId: z.number().int().positive() })).mutation(({ input }) => { try { return approveTransferOffer(input.offerId); } catch (error) { throw toTrpcError(error); } }),
  transferLoan: publicProcedure.input(z.object({ playerId: z.number().int().positive(), fromClubId: z.number().int().positive(), startDate: z.string(), endDate: z.string(), loanFee: z.number().int().nonnegative().optional(), optionFee: z.number().int().nonnegative().optional(), optionDeadline: z.string().optional() })).mutation(({ input }) => { try { return createTransferLoan({ player_id: input.playerId, from_club_id: input.fromClubId, start_date: input.startDate, end_date: input.endDate, loan_fee: input.loanFee ?? 0, option_fee: input.optionFee, option_deadline: input.optionDeadline }); } catch (error) { throw toTrpcError(error); } }),
  health: publicProcedure.input(z.object({ severity: z.string().optional(), maxDays: z.number().int().positive().optional() }).optional()).query(({ input }) => { try { return listHealth(input?.severity, input?.maxDays); } catch (error) { throw toTrpcError(error); } }),
  healthAlerts: publicProcedure.query(() => { try { return listHealthAlerts(); } catch (error) { throw toTrpcError(error); } }),
  registerInjury: publicProcedure.input(z.object({ playerId: z.number().int().positive(), injuryType: z.string().min(1), severity: z.enum(["MINOR", "MODERATE", "SEVERE"]), season: z.number().int().positive(), week: z.number().int().min(1).max(53), seed: z.number().int().optional() })).mutation(({ input }) => { try { return registerInjury(input.playerId, input.injuryType, input.severity, input.season, input.week, input.seed); } catch (error) { throw toTrpcError(error); } }),
  recoverPlayers: publicProcedure.input(z.object({ days: z.number().int().positive().default(1) })).mutation(({ input }) => { try { return recoverPlayers(input.days); } catch (error) { throw toTrpcError(error); } }),
  registerSuspension: publicProcedure.input(z.object({ playerId: z.number().int().positive(), cards: z.number().int().min(0), redCard: z.boolean(), season: z.number().int().positive(), week: z.number().int().min(1).max(53) })).mutation(({ input }) => { try { return registerSuspension(input.playerId, input.cards, input.redCard, input.season, input.week); } catch (error) { throw toTrpcError(error); } }),
  moraleSummary: publicProcedure.query(() => { try { return getMoraleSummary(); } catch (error) { throw toTrpcError(error); } }),
  formRecommendations: publicProcedure.query(() => { try { return getFormRecommendations(); } catch (error) { throw toTrpcError(error); } }),
  weeklyLoad: publicProcedure.input(z.object({ season: z.number().int().positive(), week: z.number().int().min(1).max(53) })).query(({ input }) => { try { return getWeeklyLoad(input.season, input.week); } catch (error) { throw toTrpcError(error); } }),
  upgradeDepartment: publicProcedure.input(z.object({ department: z.enum(["base", "medicina", "preparacao_fisica", "analise"]) })).mutation(({ input }) => {
    try { return upgradeClubDepartment(input.department); } catch (error) { throw toTrpcError(error); }
  }),
});
