import { execFileSync } from "node:child_process";

const ENGINE_ROOT = "/home/ubuntu/brasfoot_engine";
const GATEWAY_PATH = `${ENGINE_ROOT}/scripts/career_gateway.py`;
const DEFAULT_ENGINE_STATE_PATH = `${ENGINE_ROOT}/data/state/game.db`;

export type CareerTargetType = "club" | "selection";

export type CareerCatalogItem = {
  entityId: number;
  name: string;
  mappingStatus: string;
  assetUrl: string | null;
  assetKind: "crest" | "kit" | null;
};

type GatewayResult = { ok: boolean; error?: string } & Record<string, unknown>;

function callGateway<T extends GatewayResult>(action: "catalog" | "current" | "start", payload: Record<string, unknown>, databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH): T {
  try {
    const output = execFileSync("python3", [GATEWAY_PATH, action, "--database", databasePath], {
      input: JSON.stringify(payload),
      encoding: "utf8",
      timeout: 10_000,
      maxBuffer: 1024 * 1024,
    });
    return JSON.parse(output) as T;
  } catch (error) {
    console.error("[Career gateway] Falha ao executar ação de carreira:", error);
    return { ok: false, error: "CAREER_GATEWAY_UNAVAILABLE" } as T;
  }
}

export function listCareerTargets(targetType: CareerTargetType, search: string, limit: number, databasePath?: string) {
  const result = callGateway<{ ok: boolean; error?: string; items?: CareerCatalogItem[] }>("catalog", {
    entity_type: targetType,
    search,
    limit,
  }, databasePath);
  if (!result.ok) throw new Error(result.error || "CAREER_CATALOG_UNAVAILABLE");
  return result.items || [];
}

export function getCurrentCareer(databasePath?: string) {
  const result = callGateway<GatewayResult & { started?: boolean }>("current", {}, databasePath);
  if (!result.ok) throw new Error(result.error || "CAREER_STATE_UNAVAILABLE");
  return result;
}

export function startCareer(input: {
  managerName: string;
  nationality?: string;
  age: number;
  careerName: string;
  targetType: CareerTargetType;
  targetId: number;
}, databasePath?: string) {
  const result = callGateway<GatewayResult & { started?: boolean }>("start", {
    manager_name: input.managerName,
    nationality: input.nationality || null,
    age: input.age,
    career_name: input.careerName,
    target_type: input.targetType,
    target_id: input.targetId,
  }, databasePath);
  if (!result.ok) throw new Error(result.error || "CAREER_START_UNAVAILABLE");
  return result;
}
