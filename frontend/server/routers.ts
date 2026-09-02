import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, router } from "./_core/trpc";
import { assetsRouter } from "./routers/assets";
import { careerRouter } from "./routers/career";
import { clubRouter } from "./routers/club";
import { eventsRouter } from "./routers/events";
import { matchesRouter } from "./routers/matches";
import { staffMarketRouter } from "./routers/staffMarket";
import { sponsorshipRouter } from "./routers/sponsorship";
import { stadiumRouter } from "./routers/stadium";
import { operationsRouter } from "./routers/operations";
import { savesRouter } from "./routers/saves";

export const appRouter = router({
    // if you need to use socket.io, read and register route in server/_core/index.ts, all api should start with '/api/' so that the gateway can route correctly
  system: systemRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),
  assets: assetsRouter,
  career: careerRouter,
  club: clubRouter,
  events: eventsRouter,
  matches: matchesRouter,
  staffMarket: staffMarketRouter,
  sponsorship: sponsorshipRouter,
  stadium: stadiumRouter,
  operations: operationsRouter,
  saves: savesRouter,

  // TODO: add feature routers here, e.g.
  // todo: router({
  //   list: protectedProcedure.query(({ ctx }) =>
  //     db.getUserTodos(ctx.user.id)
  //   ),
  // }),
});

export type AppRouter = typeof appRouter;
