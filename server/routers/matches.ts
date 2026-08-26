import { z } from "zod";
import { getMatchesDashboard } from "../engineState";
import { publicProcedure, router } from "../_core/trpc";

export const matchesRouter = router({
  dashboard: publicProcedure
    .input(z.object({ competitionId: z.number().int().positive().optional() }).optional())
    .query(({ input }) => getMatchesDashboard(input?.competitionId)),
});
