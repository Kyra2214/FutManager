import { TRPCError } from "@trpc/server";
import { z } from "zod";
import { acceptSponsorshipOffer, bootstrapClubSponsorships, getClubSponsorshipSummary, listSponsorshipOffers } from "../careerGateway";
import { protectedProcedure, publicProcedure, router } from "../_core/trpc";

function toTrpcError(error: unknown) {
  const message = error instanceof Error ? error.message : "SPONSORSHIP_ACTION_FAILED";
  const code = message.endsWith("NOT_FOUND") ? "NOT_FOUND" : message.endsWith("UNAVAILABLE") || message.endsWith("ACTIVE") ? "CONFLICT" : message.endsWith("NOT_MET") ? "PRECONDITION_FAILED" : "BAD_REQUEST";
  return new TRPCError({ code, message });
}

export const sponsorshipRouter = router({
  bootstrap: protectedProcedure.mutation(() => {
    try { return bootstrapClubSponsorships(); } catch (error) { throw toTrpcError(error); }
  }),
  summary: publicProcedure.query(() => {
    try { return getClubSponsorshipSummary(); } catch (error) { throw toTrpcError(error); }
  }),
  offers: publicProcedure.query(() => {
    try { return listSponsorshipOffers(); } catch (error) { throw toTrpcError(error); }
  }),
  accept: protectedProcedure.input(z.object({ offerId: z.number().int().positive() })).mutation(({ input }) => {
    try { return acceptSponsorshipOffer(input.offerId); } catch (error) { throw toTrpcError(error); }
  }),
});
