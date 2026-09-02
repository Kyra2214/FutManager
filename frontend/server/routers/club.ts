import { getClubFinanceLedger, getClubWorkspaceDashboard, getPlayerContracts, getPlayerProfile, comparePlayerEvolution, previewContractRenewal } from "../engineState";
import { getCurrentLogicalSeason } from "../careerRead";
import { approvePlayerContractRenewal, getClubFinanceAlert, getClubFinanceAudit } from "../careerGateway";
import { protectedProcedure, publicProcedure, router } from "../_core/trpc";
import { z } from "zod";

export const clubRouter = router({
  workspace: publicProcedure.query(() => getClubWorkspaceDashboard()),
  contractRenewalPreview: publicProcedure.input(z.object({ playerId: z.number().int().positive(), clubId: z.number().int().positive(), proposedWeeklySalary: z.number().int().min(0) })).query(({ input }) => previewContractRenewal(input.playerId, input.clubId, input.proposedWeeklySalary)),
  contractRenewalApprove: protectedProcedure.input(z.object({ playerId: z.number().int().positive(), season: z.number().int().positive(), week: z.number().int().min(1).max(52), weeklySalary: z.number().int().min(0), durationWeeks: z.number().int().min(1).max(260).optional(), signingFee: z.number().int().min(0).optional(), bonus: z.number().int().min(0).optional(), managerApproved: z.literal(true), tickId: z.string().trim().min(1).optional() })).mutation(({ input }) => approvePlayerContractRenewal({ ...input })),
  playerEvolution: publicProcedure.input(z.object({ playerId: z.number().int().positive(), season: z.number().int().positive().optional() })).query(({ input }) => comparePlayerEvolution(input.playerId, input.season)),
  playerProfile: publicProcedure.input(z.object({ playerId: z.number().int().positive(), season: z.number().int().positive().optional() })).query(({ input }) => getPlayerProfile(input.playerId, input.season)),
  contracts: publicProcedure.input(z.object({ clubId: z.number().int().positive(), season: z.number().int().positive().optional(), week: z.number().int().min(1).max(52).optional(), withinWeeks: z.number().int().min(0).max(52).optional() })).query(({ input }) => getPlayerContracts(input.clubId, input.season, input.week, input.withinWeeks)),
  finance: publicProcedure.query(() => getClubWorkspaceDashboard().finance),
  financeHistory: publicProcedure.input(z.object({ season: z.number().int().min(1).optional() }).optional()).query(({ input }) => getClubFinanceAudit(input?.season ?? getCurrentLogicalSeason())),
  financeAlert: publicProcedure.input(z.object({ thresholdWeeks: z.number().int().min(1).max(52).optional() }).optional()).query(({ input }) => getClubFinanceAlert(input?.thresholdWeeks ?? 4)),
  financeLedger: publicProcedure.input(z.object({ season: z.number().int().optional(), category: z.string().trim().min(1).optional() }).optional()).query(({ input }) => getClubFinanceLedger(input?.season, input?.category)),
});
