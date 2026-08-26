import { z } from "zod";
import { getMatchesDashboard, getPlayerSeasonTotals } from "../engineState";
import { getTravelSummary, previewTravelCost } from "../careerGateway";
import { publicProcedure, router } from "../_core/trpc";

export const matchesRouter = router({
  dashboard: publicProcedure
    .input(z.object({ competitionId: z.number().int().positive().optional() }).optional())
    .query(({ input }) => getMatchesDashboard(input?.competitionId)),
  playerStats: publicProcedure
    .input(z.object({ competitionId: z.number().int().positive().optional(), matchIds: z.array(z.number().int().positive()).max(1000).optional() }).optional())
    .query(({ input }) => getPlayerSeasonTotals(input?.competitionId, input?.matchIds)),
  travelPreview: publicProcedure
    .input(z.object({ matchId: z.number().int().positive(), clubId: z.number().int().positive().optional() }))
    .query(({ input }) => previewTravelCost(input.matchId, input.clubId)),
  travelSummary: publicProcedure
    .input(z.object({ season: z.number().int().positive().optional() }).optional())
    .query(({ input }) => getTravelSummary(input?.season)),
});
