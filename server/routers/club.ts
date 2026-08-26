import { getClubFinanceLedger, getClubWorkspaceDashboard } from "../engineState";
import { getClubFinanceAlert, getClubFinanceAudit } from "../careerGateway";
import { publicProcedure, router } from "../_core/trpc";
import { z } from "zod";

export const clubRouter = router({
  workspace: publicProcedure.query(() => getClubWorkspaceDashboard()),
  finance: publicProcedure.query(() => getClubWorkspaceDashboard().finance),
  financeHistory: publicProcedure.input(z.object({ season: z.number().int().min(1).optional() }).optional()).query(({ input }) => getClubFinanceAudit(input?.season ?? 2026)),
  financeAlert: publicProcedure.input(z.object({ thresholdWeeks: z.number().int().min(1).max(52).optional() }).optional()).query(({ input }) => getClubFinanceAlert(input?.thresholdWeeks ?? 4)),
  financeLedger: publicProcedure.input(z.object({ season: z.number().int().optional(), category: z.string().trim().min(1).optional() }).optional()).query(({ input }) => getClubFinanceLedger(input?.season, input?.category)),
});
