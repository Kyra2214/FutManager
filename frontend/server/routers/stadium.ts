import { TRPCError } from "@trpc/server";
import { z } from "zod";
import { advanceWorldWeek, bootstrapClubStadium, configureClubTicketPrice, getClubStadiumSummary, getFanSegments, getSocialTimeline, previewStadiumUpgrade, previewTicketPrice, upgradeClubStadium } from "../careerGateway";
import { publicProcedure, router } from "../_core/trpc";

function toTrpcError(error: unknown) {
  const message = error instanceof Error ? error.message : "STADIUM_ACTION_FAILED";
  const code = message.includes("NOT_FOUND") ? "NOT_FOUND" : message.includes("NOT_INITIALIZED") || message.includes("INSUFFICIENT") || message.includes("MAX_LEVEL") ? "PRECONDITION_FAILED" : "BAD_REQUEST";
  return new TRPCError({ code, message });
}

export const stadiumRouter = router({
  summary: publicProcedure.query(() => { try { return getClubStadiumSummary(); } catch (error) { throw toTrpcError(error); } }),
  bootstrap: publicProcedure.mutation(() => { try { return bootstrapClubStadium(); } catch (error) { throw toTrpcError(error); } }),
  preview: publicProcedure.input(z.object({ component: z.enum(["arquibancada", "campo", "estrutura", "equipes"]) })).query(({ input }) => { try { return previewStadiumUpgrade(input.component); } catch (error) { throw toTrpcError(error); } }),
  upgrade: publicProcedure.input(z.object({ component: z.enum(["arquibancada", "campo", "estrutura", "equipes"]) })).mutation(({ input }) => { try { return upgradeClubStadium(input.component); } catch (error) { throw toTrpcError(error); } }),
  ticketPrice: publicProcedure.input(z.object({ basePrice: z.number().int().min(1).max(2000) })).mutation(({ input }) => { try { return configureClubTicketPrice(input.basePrice); } catch (error) { throw toTrpcError(error); } }),
  ticketPricePreview: publicProcedure.input(z.object({ basePrice: z.number().int().min(1).max(2000), importance: z.number().int().min(0).max(100).optional(), visitorReputation: z.number().int().min(0).max(100).optional() })).query(({ input }) => { try { return previewTicketPrice(input.basePrice, input.importance, input.visitorReputation); } catch (error) { throw toTrpcError(error); } }),
  fanSegments: publicProcedure.query(() => { try { return getFanSegments(); } catch (error) { throw toTrpcError(error); } }),
  socialTimeline: publicProcedure.input(z.object({ limit: z.number().int().min(1).max(100).optional(), offset: z.number().int().min(0).optional() }).optional()).query(({ input }) => { try { return getSocialTimeline(input?.limit, input?.offset); } catch (error) { throw toTrpcError(error); } }),
  advanceWeek: publicProcedure.input(z.object({ seed: z.number().int().optional() }).optional()).mutation(({ input }) => { try { return advanceWorldWeek(input?.seed); } catch (error) { throw toTrpcError(error); } }),
});
