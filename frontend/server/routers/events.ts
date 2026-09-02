import { TRPCError } from "@trpc/server";
import { z } from "zod";
import { listClubEvents, markClubEventRead } from "../careerGateway";
import { protectedProcedure, publicProcedure, router } from "../_core/trpc";

function toTrpcError(error: unknown) {
  const message = error instanceof Error ? error.message : "CLUB_EVENTS_ACTION_FAILED";
  return new TRPCError({ code: message.includes("NOT_FOUND") ? "NOT_FOUND" : "BAD_REQUEST", message });
}

export const eventsRouter = router({
  list: publicProcedure.input(z.object({ limit: z.number().int().min(1).max(100).default(20), unreadOnly: z.boolean().default(false) }).optional()).query(({ input }) => {
    try { return listClubEvents(input?.limit ?? 20, input?.unreadOnly ?? false); } catch (error) { throw toTrpcError(error); }
  }),
  markRead: protectedProcedure.input(z.object({ eventId: z.number().int().positive() })).mutation(({ input }) => {
    try { return markClubEventRead(input.eventId); } catch (error) { throw toTrpcError(error); }
  }),
});
