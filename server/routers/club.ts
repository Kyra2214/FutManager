import { getClubFinanceLedger, getClubWorkspaceDashboard } from "../engineState";
import { publicProcedure, router } from "../_core/trpc";
import { z } from "zod";

export const clubRouter = router({
  workspace: publicProcedure.query(() => getClubWorkspaceDashboard()),
  finance: publicProcedure.query(() => getClubWorkspaceDashboard().finance),
  financeLedger: publicProcedure.input(z.object({ season: z.number().int().optional(), category: z.string().trim().min(1).optional() }).optional()).query(({ input }) => getClubFinanceLedger(input?.season, input?.category)),
});
