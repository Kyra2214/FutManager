import { getClubWorkspaceDashboard } from "../engineState";
import { publicProcedure, router } from "../_core/trpc";

export const clubRouter = router({
  workspace: publicProcedure.query(() => getClubWorkspaceDashboard()),
});
