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
type GatewayAction = "catalog" | "current" | "start" | "economy_bootstrap" | "economy_summary" | "staff_catalog" | "staff_hire" | "department_offers" | "department_upgrade" | "economy_weekly" | "sponsor_bootstrap" | "sponsor_summary" | "sponsor_offers" | "sponsor_accept";

function callGateway<T extends GatewayResult>(action: GatewayAction, payload: Record<string, unknown>, databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH): T {
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

function staffMarketAction<T extends GatewayResult>(action: Exclude<GatewayAction, "catalog" | "current" | "start">, payload: Record<string, unknown> = {}, databasePath?: string): T {
  const result = callGateway<T>(action, payload, databasePath);
  if (!result.ok) throw new Error(result.error || "STAFF_MARKET_UNAVAILABLE");
  return result;
}

export function bootstrapClubEconomy(databasePath?: string) {
  return staffMarketAction<GatewayResult & { cash: number; budget: number; payroll: number; weekly_player_payroll: number; weekly_staff_payroll: number; weekly_department_maintenance: number; initial_cash: number; team_power: number; country_factor: number; base_level: number }>("economy_bootstrap", {}, databasePath);
}

export function getClubEconomySummary(databasePath?: string) {
  return staffMarketAction<GatewayResult & { cash: number; budget: number; payroll: number; expense_accumulated: number; weekly_player_payroll: number; weekly_staff_payroll: number; weekly_department_maintenance: number; weekly_total: number; initial_cash: number; team_power: number; country_factor: number; base_level: number }>("economy_summary", {}, databasePath);
}

export function listAvailableStaff(role?: string, databasePath?: string) {
  return staffMarketAction<GatewayResult & { items: Array<{ staff_id: number; name: string; role: string; age: number; experience: number; reputation: number; level: number; potential: number; specialization: string | null; weekly_salary: number }> }>("staff_catalog", { role }, databasePath).items;
}

export function hireAvailableStaff(staffId: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { staff_id: number; name: string; role: string; weekly_salary: number; payroll: number }>("staff_hire", { staff_id: staffId }, databasePath);
}

export function listDepartmentOffers(databasePath?: string) {
  return staffMarketAction<GatewayResult & { items: Array<{ department: string; label: string; target_level: number; cost: number; maintenance: number; capacity: number }> }>("department_offers", {}, databasePath).items;
}

export function upgradeClubDepartment(department: string, databasePath?: string) {
  return staffMarketAction<GatewayResult & { department: string; label: string; target_level: number; cost: number; maintenance: number; capacity: number }>("department_upgrade", { department }, databasePath);
}

export type SponsorOffer = {
  offer_id: number;
  star_rating: number;
  minimum_overall: number;
  upfront_payment: number;
  weekly_payment: number;
  mission_bonus: number;
  contract_weeks: number;
  status: string;
  name: string;
  industry: string;
  expires_season: number;
  expires_week: number;
  source_overall: number;
  source_stars: number;
};

export type SponsorshipSummary = {
  club_id: number;
  institutional_overall: number;
  sponsor_stars: number;
  institutional_profile: { squad_score: number; ct_score: number; stadium_score: number; squad_available: boolean; ct_available: boolean; stadium_available: boolean };
  active_contract: { contract_id: number; sponsor_id: number; name: string; industry: string; star_rating: number; upfront_payment: number; weekly_payment: number; mission_bonus: number; end_season: number; end_week: number; status: string } | null;
  offers: SponsorOffer[];
  missions: Array<{ mission_id: number; title: string; mission_type: string; target_value: number; current_value: number; reward: number; status: string; deadline_season: number; deadline_week: number }>;
};

export function bootstrapClubSponsorships(databasePath?: string) {
  return staffMarketAction<GatewayResult & SponsorshipSummary>("sponsor_bootstrap", {}, databasePath);
}

export function getClubSponsorshipSummary(databasePath?: string) {
  return staffMarketAction<GatewayResult & SponsorshipSummary>("sponsor_summary", {}, databasePath);
}

export function listSponsorshipOffers(databasePath?: string) {
  return staffMarketAction<GatewayResult & { items: SponsorOffer[] }>("sponsor_offers", {}, databasePath).items;
}

export function acceptSponsorshipOffer(offerId: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { contract_id: number; sponsor: string; star_rating: number; upfront_payment: number; weekly_payment: number; end_season: number; end_week: number }>("sponsor_accept", { offer_id: offerId }, databasePath);
}
