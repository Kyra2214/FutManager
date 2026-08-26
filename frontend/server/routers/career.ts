import { TRPCError } from "@trpc/server";
import { z } from "zod";
import { getCurrentCareer, listCareerTargets, startCareer } from "../careerGateway";
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
  catalog: publicProcedure
    .input(z.object({ targetType: z.enum(["club", "selection"]), search: z.string().max(120).default(""), limit: z.number().int().min(1).max(96).default(48) }))
    .query(({ input }) => {
      try {
        return listCareerTargets(input.targetType, input.search.trim(), input.limit);
      } catch (error) {
        throw toTrpcError(error);
      }
    }),
  start: publicProcedure
    .input(z.object({ managerName: z.string().trim().min(1).max(60), nationality: z.string().trim().max(60).optional(), age: z.number().int().min(18).max(90), careerName: z.string().trim().min(1).max(80), targetType: z.enum(["club", "selection"]), targetId: z.number().int().positive() }))
    .mutation(({ input }) => {
      try {
        return startCareer(input);
      } catch (error) {
        throw toTrpcError(error);
      }
    }),
});
