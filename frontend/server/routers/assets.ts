import { z } from "zod";
import { getEntityAssetLink } from "../engineState";
import { publicProcedure, router } from "../_core/trpc";

export const assetsRouter = router({
  resolve: publicProcedure
    .input(z.object({ entityType: z.enum(["team", "selection"]), entityId: z.number().int().positive() }))
    .query(({ input }) => getEntityAssetLink(input.entityType, input.entityId)),
});
