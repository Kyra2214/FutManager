import type { CreateExpressContextOptions } from "@trpc/server/adapters/express";
import type { User } from "../../drizzle/schema";
import { sdk } from "./sdk";
import { DEFAULT_SAVE_SLOT, SAVE_SLOT_COOKIE, resolveSaveDatabasePath } from "../saveManager";

export type TrpcContext = {
  req: CreateExpressContextOptions["req"];
  res: CreateExpressContextOptions["res"];
  user: User | null;
  saveSlot: string;
  databasePath: string;
};

function readCookie(req: CreateExpressContextOptions["req"], name: string) {
  const raw = req.headers.cookie || "";
  const prefix = `${name}=`;
  const item = raw.split(";").map(part => part.trim()).find(part => part.startsWith(prefix));
  return item ? decodeURIComponent(item.slice(prefix.length)) : undefined;
}

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

  const requestedSlot = readCookie(opts.req, SAVE_SLOT_COOKIE) || DEFAULT_SAVE_SLOT;
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

  return {
    req: opts.req,
    res: opts.res,
    user,
    saveSlot,
    databasePath,
  };
}
