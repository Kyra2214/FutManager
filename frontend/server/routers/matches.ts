import { z } from "zod";
import { getMatchesDashboard, getPlayerSeasonTotals } from "../engineState";
import { publicProcedure, router } from "../_core/trpc";

export const matchesRouter = router({
  dashboard: publicProcedure
    .input(z.object({ competitionId: z.number().int().positive().optional() }).optional())
    .query(({ input }) => getMatchesDashboard(input?.competitionId)),
  playerStats: publicProcedure
    .input(z.object({ competitionId: z.number().int().positive().optional(), matchIds: z.array(z.number().int().positive()).max(1000).optional() }).optional())
    .query(({ input }) => getPlayerSeasonTotals(input?.competitionId, input?.matchIds)),
});
