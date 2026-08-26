import { z } from "zod";
import { protectedProcedure, router } from "../_core/trpc";
import { runCareerGatewayAction } from "../careerGateway";
import { TRPCError } from "@trpc/server";

function toTrpcError(error: unknown): never {
  const message = error instanceof Error ? error.message : "CAREER_OPERATION_FAILED";
  const code = message.includes("NOT_FOUND") ? "NOT_FOUND" : message.includes("PERMISSION") || message.includes("CAREER_NOT_STARTED") ? "FORBIDDEN" : "BAD_REQUEST";
  throw new TRPCError({ code, message });
}

function action<T extends { ok: boolean; error?: string } & Record<string, unknown>>(name: Parameters<typeof runCareerGatewayAction>[0], payload: Record<string, unknown> = {}) {
  try {
    return runCareerGatewayAction<T>(name, payload);
  } catch (error) {
    return toTrpcError(error);
  }
}

export const operationsRouter = router({
  snapshots: router({
    list: protectedProcedure.query(() => action("career_snapshot_list")),
    create: protectedProcedure.mutation(() => action<{ ok: boolean; snapshot_id: number }>("career_snapshot")),
    hash: protectedProcedure.input(z.object({ snapshotId: z.number().int().positive() })).query(({ input }) => action("career_snapshot_hash", { snapshot_id: input.snapshotId })),
    compare: protectedProcedure.input(z.object({ leftId: z.number().int().positive(), rightId: z.number().int().positive() })).query(({ input }) => action("career_snapshot_compare", { left_id: input.leftId, right_id: input.rightId })),
    restore: protectedProcedure.input(z.object({ snapshotId: z.number().int().positive(), fields: z.array(z.enum(["current_club_id", "season_id", "status", "name"])).min(1).max(4) })).mutation(({ input }) => action("career_snapshot_restore", { snapshot_id: input.snapshotId, fields: input.fields })),
    audit: protectedProcedure.query(() => action("career_snapshot_audit")),
  }),
  simulation: router({
    progress: protectedProcedure.input(z.object({ tickId: z.string().min(1).max(120) })).query(({ input }) => action("simulation_progress", { tick_id: input.tickId })),
    metrics: protectedProcedure.input(z.object({ tickId: z.string().min(1).max(120) })).query(({ input }) => action("simulation_metrics", { tick_id: input.tickId })),
    failureReport: protectedProcedure.input(z.object({ tickId: z.string().min(1).max(120) })).query(({ input }) => action("simulation_failure_report", { tick_id: input.tickId })),
    batch: protectedProcedure.input(z.object({ tickId: z.string().min(1).max(120), level: z.enum(["FULL", "STANDARD", "FAST", "ABSTRACT"]).default("ABSTRACT"), batchSize: z.number().int().min(1).max(1000).default(100), seed: z.number().int().default(0) })).mutation(({ input }) => action("simulation_batch", { tick_id: input.tickId, level: input.level, batch_size: input.batchSize, seed: input.seed })),
    resume: protectedProcedure.input(z.object({ tickId: z.string().min(1).max(120), level: z.enum(["FULL", "STANDARD", "FAST", "ABSTRACT"]).default("ABSTRACT"), batchSize: z.number().int().min(1).max(1000).default(100), seed: z.number().int().default(0) })).mutation(({ input }) => action("simulation_resume", { tick_id: input.tickId, level: input.level, batch_size: input.batchSize, seed: input.seed })),
  }),
  finance: router({
    monthlyClose: protectedProcedure.input(z.object({ season: z.number().int().min(1900).max(2200), month: z.number().int().min(1).max(12) })).query(({ input }) => action("finance_monthly_close", input)),
    reconciliation: protectedProcedure.input(z.object({ season: z.number().int().min(1900).max(2200), sourceTypes: z.array(z.string().min(1).max(40)).max(20).optional() })).query(({ input }) => action("finance_reconciliation", { season: input.season, source_types: input.sourceTypes })),
    mediaSummary: protectedProcedure.input(z.object({ season: z.number().int().min(1900).max(2200) })).query(({ input }) => action("finance_media_summary", input)),
  }),
});
