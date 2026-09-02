import { TRPCError } from "@trpc/server";
import { z } from "zod";
import { advanceUntilControlledMatch, advanceWorldWeek, getCurrentCareer, getParallelLeaguePreview, listCareerTargets, listWorldCountries, startCareer } from "../careerGateway";
import { listTeamCatalog } from "../teamCatalog";
import { publicProcedure, router } from "../_core/trpc";

function toTrpcError(error: unknown) {
  const message = error instanceof Error ? error.message : "CAREER_ACTION_FAILED";
  const code = message === "ACTIVE_CAREER_EXISTS" ? "CONFLICT" : message.endsWith("NOT_FOUND") ? "NOT_FOUND" : "BAD_REQUEST";
  return new TRPCError({ code, message });
}

export const careerRouter = router({
  current: publicProcedure.query(() => {
    try {
      return getCurrentCareer();
    } catch (error) {
      throw toTrpcError(error);
    }
  }),
  worldCountries: publicProcedure
    .input(z.object({ search: z.string().max(120).default(""), limit: z.number().int().min(1).max(96).default(48) }))
    .query(({ input }) => {
      try {
        return { items: listWorldCountries(input.search.trim(), input.limit) };
      } catch (error) {
        throw toTrpcError(error);
      }
    }),
  catalog: publicProcedure
    .input(z.object({ targetType: z.enum(["club", "selection"]), search: z.string().max(120).default(""), limit: z.number().int().min(1).max(96).default(48) }))
    .query(({ input }) => {
      try {
        if (input.targetType === "club") return listTeamCatalog(input.search.trim(), input.limit);
        return listCareerTargets(input.targetType, input.search.trim(), input.limit);
      } catch (error) {
        throw toTrpcError(error);
      }
    }),
  parallelPreview: publicProcedure
    .input(z.object({ selectedCountryIds: z.array(z.number().int().positive()).min(1).max(12), targetType: z.enum(["club", "selection"]), targetId: z.number().int().positive() }))
    .query(({ input }) => {
      try {
        return getParallelLeaguePreview(input.selectedCountryIds, input.targetType, input.targetId);
      } catch (error) {
        throw toTrpcError(error);
      }
    }),
  advanceWeek: publicProcedure
    .input(z.object({ seed: z.number().int().optional() }).optional())
    .mutation(({ input }) => {
      try {
        return advanceWorldWeek(input?.seed);
      } catch (error) {
        throw toTrpcError(error);
      }
    }),
  advanceUntilMatch: publicProcedure
    .input(z.object({ matchId: z.number().int().positive(), seed: z.number().int().optional() }))
    .mutation(({ input }) => {
      try {
        return advanceUntilControlledMatch(input.matchId, input.seed);
      } catch (error) {
        throw toTrpcError(error);
      }
    }),
  start: publicProcedure
    .input(z.object({ managerName: z.string().trim().min(1).max(60), nationality: z.string().trim().max(60).optional(), age: z.number().int().min(18).max(90), careerName: z.string().trim().min(1).max(80), targetType: z.enum(["club", "selection"]), targetId: z.number().int().positive(), selectedCountryIds: z.array(z.number().int().positive()).min(1).max(12) }))
    .mutation(({ input }) => {
      try {
        return startCareer(input);
      } catch (error) {
        throw toTrpcError(error);
      }
    }),
});
