import { z } from "zod";
import { protectedProcedure, router } from "../_core/trpc";
import { SAVE_SLOT_COOKIE, createSaveSlot, deleteSaveSlot, listSaveSlots, renameSaveSlot, resolveSaveDatabasePath, touchSaveSlot } from "../saveManager";

function setSaveCookie(ctx: { req: { secure?: boolean }; res: { cookie: (name: string, value: string, options: Record<string, unknown>) => void } }, slotId: string) {
  ctx.res.cookie(SAVE_SLOT_COOKIE, slotId, {
    httpOnly: true,
    sameSite: "lax",
    secure: Boolean(ctx.req.secure),
    path: "/",
    maxAge: 1000 * 60 * 60 * 24 * 365,
  });
}

export const savesRouter = router({
  list: protectedProcedure.query(() => listSaveSlots().map(({ databasePath: _databasePath, ...slot }) => slot)),
  current: protectedProcedure.query(({ ctx }) => ({ slotId: ctx.saveSlot, slots: listSaveSlots().map(({ databasePath: _databasePath, ...slot }) => slot) })),
  select: protectedProcedure.input(z.object({ slotId: z.string().trim().min(1).max(32) })).mutation(({ ctx, input }) => {
    resolveSaveDatabasePath(input.slotId);
    setSaveCookie(ctx, input.slotId);
    touchSaveSlot(input.slotId);
    return { success: true, slotId: input.slotId };
  }),
  create: protectedProcedure.input(z.object({ name: z.string().trim().min(1).max(40) })).mutation(({ ctx, input }) => {
    const slot = createSaveSlot(input.name, ctx.saveSlot);
    setSaveCookie(ctx, slot.id);
    return { success: true, slot: { ...slot, databasePath: undefined } };
  }),
  rename: protectedProcedure.input(z.object({ slotId: z.string().trim().min(1).max(32), name: z.string().trim().min(1).max(40) })).mutation(({ input }) => renameSaveSlot(input.slotId, input.name)),
  delete: protectedProcedure.input(z.object({ slotId: z.string().trim().min(1).max(32) })).mutation(({ ctx, input }) => {
    if (ctx.saveSlot === input.slotId) {
      setSaveCookie(ctx, "default");
      touchSaveSlot("default");
    }
    return deleteSaveSlot(input.slotId);
  }),
  checkpoint: protectedProcedure.mutation(({ ctx }) => {
    touchSaveSlot(ctx.saveSlot);
    return { success: true, slotId: ctx.saveSlot, savedAt: new Date().toISOString() };
  }),
});
