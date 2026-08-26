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
type GatewayAction = "catalog" | "current" | "start" | "economy_bootstrap" | "economy_summary" | "staff_catalog" | "staff_hire" | "staff_contract" | "staff_terminate" | "staff_replace" | "department_offers" | "department_upgrade" | "economy_weekly" | "training_departments" | "training_budget" | "training_plan" | "training_development" | "training_alerts" | "sponsor_bootstrap" | "sponsor_summary" | "sponsor_offers" | "sponsor_accept" | "stadium_bootstrap" | "stadium_summary" | "stadium_upgrade" | "ticket_price" | "weekly_advance" | "events_list" | "events_mark_read";

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

export function listAvailableStaff(role?: string, minLevel?: number, maxLevel?: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { items: Array<{ staff_id: number; name: string; role: string; age: number; experience: number; reputation: number; level: number; potential: number; specialization: string | null; weekly_salary: number; cost_benefit: number }> }>("staff_catalog", { role, min_level: minLevel, max_level: maxLevel }, databasePath).items;
}

export function hireAvailableStaff(staffId: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { staff_id: number; name: string; role: string; weekly_salary: number; payroll: number; contract_id: number; end_date: string; termination_fee: number }>("staff_hire", { staff_id: staffId }, databasePath);
}

export function getStaffContract(staffId: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { contract_id: number; staff_id: number; club_id: number; start_date: string; end_date: string; weekly_salary: number; termination_fee: number; status: string }>("staff_contract", { staff_id: staffId }, databasePath);
}

export function terminateStaff(staffId: number, waiveFee = false, databasePath?: string) {
  return staffMarketAction<GatewayResult & { staff_id: number; name: string; termination_fee: number; weekly_staff_payroll: number; status: string }>("staff_terminate", { staff_id: staffId, waive_fee: waiveFee }, databasePath);
}

export function replaceStaff(outgoingStaffId: number, incomingStaffId: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { terminated: ReturnType<typeof terminateStaff>; hired: ReturnType<typeof hireAvailableStaff> }>("staff_replace", { outgoing_staff_id: outgoingStaffId, incoming_staff_id: incomingStaffId }, databasePath);
}

export function listTrainingDepartments(databasePath?: string) {
  return staffMarketAction<GatewayResult & { items: Array<{ department: string; label: string; level: number; max_level: number; purchase_base: number; maintenance: number; capacity: number; efficiency: number }> }>("training_departments", {}, databasePath).items;
}

export function listTrainingBudget(databasePath?: string) {
  return staffMarketAction<GatewayResult & { items: Array<{ department: string; next_level: number; cost: number; projected_capacity: number; maintenance: number }> }>("training_budget", {}, databasePath).items;
}

export function createTrainingPlan(season: number, week: number, planType: string, load: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { plan_id: number; club_id: number; season: number; week: number; plan_type: string; load: number; sessions: Array<{ status: string; total: number; risk: number }> }>("training_plan", { season, week, plan_type: planType, load }, databasePath);
}

export function listTrainingDevelopment(databasePath?: string) {
  return staffMarketAction<GatewayResult & { items: Array<Record<string, unknown>> }>("training_development", {}, databasePath).items;
}

export function listTrainingAlerts(databasePath?: string) {
  return staffMarketAction<GatewayResult & { items: Array<{ department: string; message: string }> }>("training_alerts", {}, databasePath).items;
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

export type StadiumSummary = {
  initialized: boolean;
  stadium: { stadium_id: number; name: string; base_capacity: number; capacity: number; maintenance: number; matchday_quality: number; components: Array<{ component: "arquibancada" | "campo" | "estrutura" | "equipes"; level: number; next_level: number | null; upgrade_cost: number | null; maintenance: number }> } | null;
  fan_base: { size: number; satisfaction: number; engagement: number; interest: number } | null;
  reputation: { sporting: number; commercial: number; national: number } | null;
  ticket_price: number;
  attendance: Array<{ match_id: number; expected_attendance: number; actual_attendance: number; ticket_price: number; revenue: number }>;
};

export function bootstrapClubStadium(databasePath?: string) {
  return staffMarketAction<GatewayResult & StadiumSummary["stadium"]>("stadium_bootstrap", {}, databasePath);
}

export function getClubStadiumSummary(databasePath?: string) {
  return staffMarketAction<GatewayResult & StadiumSummary>("stadium_summary", {}, databasePath);
}

export function upgradeClubStadium(component: StadiumSummary["stadium"] extends infer _ ? "arquibancada" | "campo" | "estrutura" | "equipes" : never, databasePath?: string) {
  return staffMarketAction<GatewayResult>("stadium_upgrade", { component }, databasePath);
}

export function configureClubTicketPrice(basePrice: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { club_id: number; base_price: number }>("ticket_price", { base_price: basePrice }, databasePath);
}

export function advanceWorldWeek(seed?: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { status: string; season: number; week: number; matches?: number }>("weekly_advance", { seed }, databasePath);
}

export type ClubEvent = {
  event_id: number;
  club_id: number;
  type: "TRANSFERENCIA" | "LESAO" | "CONTRATO" | "PATROCINIO" | "FINANCEIRO" | "COMPETICAO" | "ESTADIO" | "TORCIDA";
  origin: string | null;
  severity: "LOW" | "NORMAL" | "HIGH" | "CRITICAL";
  event_date: string;
  title: string;
  description: string | null;
  impact: string | null;
  status: "OPEN" | "READ";
  is_read: boolean;
  reference: string | null;
};

export function listClubEvents(limit = 20, unreadOnly = false, databasePath?: string) {
  return staffMarketAction<GatewayResult & { unread_count: number; items: ClubEvent[] }>("events_list", { limit, unread_only: unreadOnly }, databasePath);
}

export function markClubEventRead(eventId: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { event_id: number; read: boolean }>("events_mark_read", { event_id: eventId }, databasePath);
}
