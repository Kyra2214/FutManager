import type { CreateExpressContextOptions } from "@trpc/server/adapters/express";
import type { User } from "../../drizzle/schema";
import { sdk } from "./sdk";
import { DEFAULT_SAVE_SLOT, SAVE_SLOT_COOKIE, resolveSaveDatabasePath, touchSaveSlot } from "../saveManager";

export type TrpcContext = {
  req: CreateExpressContextOptions["req"];
  res: CreateExpressContextOptions["res"];
  user: User | null;
  saveSlot: string;
  databasePath: string;
};

export async function createContext(
  opts: CreateExpressContextOptions
): Promise<TrpcContext> {
  let user: User | null = null;

  try {
    user = await sdk.authenticateRequest(opts.req);
  } catch (error) {
    // Authentication is optional for public procedures.
    user = null;
  }

  const requestedSlot = typeof opts.req.cookies?.[SAVE_SLOT_COOKIE] === "string"
    ? opts.req.cookies[SAVE_SLOT_COOKIE]
    : DEFAULT_SAVE_SLOT;
  let saveSlot = DEFAULT_SAVE_SLOT;
  let databasePath = resolveSaveDatabasePath(DEFAULT_SAVE_SLOT);
  try {
    databasePath = resolveSaveDatabasePath(requestedSlot);
    saveSlot = requestedSlot;
  } catch {
    // A deleted/invalid slot falls back to the default save.
  }

  // The engine is intentionally single-player/local-first: one request context
  // selects the active database for the process. This keeps all existing engine
  // services on the same isolated SQLite file without duplicating every API.
  process.env.FUTMANAGER_ENGINE_STATE_PATH = databasePath;
  touchSaveSlot(saveSlot);

  return {
    req: opts.req,
    res: opts.res,
    user,
    saveSlot,
    databasePath,
  };
}
