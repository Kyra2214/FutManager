import { z } from "zod";
import { compareCompetitions, getCompetitionHistory, getMatchesDashboard, getPlayerSeasonTotals, previewClassification } from "../engineState";
import { getTravelSummary, playControlledMatch, previewTravelCost } from "../careerGateway";
import { publicProcedure, router } from "../_core/trpc";

export const matchesRouter = router({
  dashboard: publicProcedure
    .input(z.object({ competitionId: z.number().int().positive().optional(), season: z.number().int().positive().optional(), phaseId: z.number().int().positive().optional() }).optional())
    .query(({ input }) => getMatchesDashboard(input?.competitionId, input?.season, input?.phaseId)),
  competitionHistory: publicProcedure.input(z.object({ competitionId: z.number().int().positive() })).query(({ input }) => getCompetitionHistory(input.competitionId)),
  classificationPreview: publicProcedure.input(z.object({ competitionId: z.number().int().positive(), homeClubId: z.number().int().positive(), awayClubId: z.number().int().positive(), homeGoals: z.number().int().min(0).max(30), awayGoals: z.number().int().min(0).max(30) })).query(({ input }) => previewClassification(input.competitionId, input.homeClubId, input.awayClubId, input.homeGoals, input.awayGoals)),
  competitionComparison: publicProcedure.input(z.object({ competitionIds: z.array(z.number().int().positive()).max(20).optional() }).optional()).query(({ input }) => compareCompetitions(input?.competitionIds)),
  playerStats: publicProcedure
    .input(z.object({ competitionId: z.number().int().positive().optional(), matchIds: z.array(z.number().int().positive()).max(1000).optional() }).optional())
    .query(({ input }) => getPlayerSeasonTotals(input?.competitionId, input?.matchIds)),
  travelPreview: publicProcedure
    .input(z.object({ matchId: z.number().int().positive(), clubId: z.number().int().positive().optional() }))
    .query(({ input }) => previewTravelCost(input.matchId, input.clubId)),
  travelSummary: publicProcedure
    .input(z.object({ season: z.number().int().positive().optional() }).optional())
    .query(({ input }) => getTravelSummary(input?.season)),
  playControlled: publicProcedure
    .input(z.object({
      matchId: z.number().int().positive(),
      seed: z.number().int().optional(),
      decisions: z.object({
        tactics: z.object({ mentality: z.string(), attackLane: z.string(), passing: z.string(), pressure: z.string(), crossing: z.boolean() }).optional(),
        substitutions: z.array(z.object({ playerOutId: z.number().int().positive(), playerInId: z.number().int().positive() })).max(5).optional(),
        penalty_taker_id: z.number().int().positive().optional(),
        red_card_response: z.object({ formation: z.string(), mentality: z.string() }).optional(),
      }).optional(),
    }))
    .mutation(({ input }) => playControlledMatch(input.matchId, input.seed, input.decisions)),
});
