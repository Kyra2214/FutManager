import { execFileSync } from "node:child_process";

const ENGINE_ROOT = process.env.FUTMANAGER_ENGINE_ROOT || "/home/ubuntu/brasfoot_engine";
const GATEWAY_PATH = `${ENGINE_ROOT}/scripts/career_gateway.py`;
const DEFAULT_ENGINE_STATE_PATH = `${ENGINE_ROOT}/data/state/game.db`;

export type CareerTargetType = "club" | "selection";

export type CareerCatalogItem = {
  entityId: number;
  name: string;
  countryId?: number | null;
  mappingStatus: string;
  assetUrl: string | null;
  assetKind: "crest" | "kit" | null;
};

export type WorldCountry = { countryId: number; name: string; code: string | null; clubCount: number; firstDivisionClubCount: number; firstDivisionName: string | null };

type GatewayResult = { ok: boolean; error?: string } & Record<string, unknown>;
export type ParallelLeagueSnapshot = { league: { career_id: number; name: string; total_clubs: number; source_country_count: number; seed: string; division_count: number }; season_number: number; fixture_count: number; played_count: number; standings: Array<Record<string, unknown>>; fixtures: Array<Record<string, unknown>> };

export type GatewayAction = "p0_contracts" | "p0_contract_validate" | "p0_contract_audit" | "p1_procedure_contracts" | "p1_procedure_validate" | "p1_procedure_audit" | "parallel_preview" | "parallel_snapshot" | "parallel_result" | "parallel_close" | "catalog" | "current" | "start" | "contract_renew_approve" | "economy_bootstrap" | "economy_summary" | "staff_catalog" | "staff_hire" | "staff_contract" | "staff_terminate" | "staff_replace" | "department_offers" | "department_upgrade" | "economy_weekly" | "finance_revenue" | "finance_expense" | "finance_budget" | "finance_expense_preview" | "finance_post_match_preview" | "finance_projection" | "finance_alert" | "finance_world_report" | "finance_audit" | "finance_monthly_close" | "finance_reconciliation" | "finance_media_summary" | "travel_preview" | "travel_summary" | "training_departments" | "morale_summary" | "morale_match" | "weekly_training" | "opponent_preparation" | "weekly_load" | "form_recommendations" | "health_list" | "health_alerts" | "health_injury" | "health_recover" | "health_suspension" | "ai_diagnosis" | "ai_history" | "ai_training" | "ai_market" | "ai_weekly" | "ai_lineup" | "ai_tactic" | "ai_objective_progress" | "training_budget" | "training_plan" | "training_development" | "training_alerts" | "sponsor_bootstrap" | "sponsor_summary" | "sponsor_offers" | "sponsor_accept" | "stadium_bootstrap" | "stadium_summary" | "stadium_preview" | "stadium_upgrade" | "ticket_price" | "ticket_price_preview" | "fan_segments" | "social_timeline" | "weekly_advance" | "play_controlled_match" | "events_list" | "events_mark_read" | "transferable_players" | "transfer_open_window" | "transfer_preview" | "transfer_offer" | "transfer_counter" | "transfer_accept" | "transfer_approve" | "transfer_loan" | "transfer_complete" | "simulation_configure" | "simulation_batch" | "simulation_progress" | "simulation_checkpoint" | "simulation_divergence" | "simulation_benchmark" | "simulation_resume" | "simulation_metrics" | "simulation_failure_report" | "scout_regions" | "scout_create_region" | "scout_mission" | "scout_start" | "scout_complete" | "scout_opportunities" | "scout_compare" | "scout_confirm" | "academy_enroll" | "academy_progress" | "academy_promote" | "academy_maintenance" | "sponsor_weekly" | "training_objective" | "training_preview" | "training_approve" | "training_cancel" | "transfer_history" | "transfer_alerts" | "transfer_expire" | "ai_preview" | "ai_approve" | "ai_risk_limit" | "ai_budget_alerts" | "health_return_protocol" | "health_eligibility" | "health_treatment" | "health_audit" | "training_microcycle" | "training_overtraining" | "training_audit" | "career_snapshot" | "career_snapshot_list" | "career_snapshot_hash" | "career_snapshot_compare" | "career_snapshot_restore" | "career_snapshot_audit" | "gateway_audit";

function callGateway<T extends GatewayResult>(action: GatewayAction, payload: Record<string, unknown>, databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH): T {
  try {
    const output = execFileSync("python3", [GATEWAY_PATH, action, "--database", databasePath], {
      input: JSON.stringify(payload),
      encoding: "utf8",
      timeout: 60_000,
      maxBuffer: 8 * 1024 * 1024,
    });
    return JSON.parse(output) as T;
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    console.warn(`[Career gateway] Ação ${action} indisponível: ${detail.slice(0, 180)}`);
    return { ok: false, error: "CAREER_GATEWAY_UNAVAILABLE" } as T;
  }
}

export function runCareerGatewayAction<T extends GatewayResult = GatewayResult>(action: GatewayAction, payload: Record<string, unknown> = {}, databasePath?: string): T {
  const result = callGateway<T>(action, payload, databasePath);
  if (!result.ok) throw new Error(result.error || `CAREER_ACTION_FAILED:${action}`);
  return result;
}

export function listWorldCountries(search = "", limit = 48, databasePath?: string) {
  const result = callGateway<{ ok: boolean; error?: string; items?: WorldCountry[] }>("catalog", { entity_type: "world_country", search, limit }, databasePath);
  if (!result.ok) throw new Error(result.error || "WORLD_COUNTRY_CATALOG_UNAVAILABLE");
  return result.items || [];
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

export function listP0Contracts(domainId?: number, databasePath?: string) {
  return runCareerGatewayAction<{ ok: boolean; items: Array<Record<string, unknown>> }>("p0_contracts", domainId === undefined ? {} : { domain_id: domainId }, databasePath).items;
}

export function validateP0Contract(itemId: number, databasePath?: string) {
  return runCareerGatewayAction<{ ok: boolean; status: string; item_id: number; checks: Record<string, boolean>; contract: Record<string, unknown> }>("p0_contract_validate", { item_id: itemId }, databasePath);
}

export function auditP0Contracts(databasePath?: string) {
  return runCareerGatewayAction<{ ok: boolean; status: string; contract_count: number; checks: Record<string, boolean>; invalid_items: number[]; read_only: boolean }>("p0_contract_audit", {}, databasePath);
}

export function listP1ProcedureContracts(databasePath?: string) {
  return runCareerGatewayAction<{ ok: boolean; items: Array<Record<string, unknown>> }>("p1_procedure_contracts", {}, databasePath).items;
}

export function validateP1Procedure(itemId: number, databasePath?: string) {
  return runCareerGatewayAction<{ ok: boolean; status: string; item_id: number; checks: Record<string, boolean>; contract: Record<string, unknown> }>("p1_procedure_validate", { item_id: itemId }, databasePath);
}

export function auditP1Procedures(databasePath?: string) {
  return runCareerGatewayAction<{ ok: boolean; status: string; procedure_count: number; checks: Record<string, boolean>; invalid_items: number[]; read_only: boolean }>("p1_procedure_audit", {}, databasePath);
}

export function getCurrentCareer(databasePath?: string) {
  const result = callGateway<GatewayResult & { started?: boolean }>("current", {}, databasePath);
  if (!result.ok) throw new Error(result.error || "CAREER_STATE_UNAVAILABLE");
  return result;
}

export function getParallelLeaguePreview(selectedCountryIds: number[], targetType: CareerTargetType, targetId: number, databasePath?: string) {
  const result = callGateway<GatewayResult & { total_clubs: number; country_count: number; division_count: number; seed: string; target_division: number | null; divisions: Array<{ division: number; clubs: Array<{ club_id: number; origin_country_id: number; name: string }> }>; read_only: boolean }>("parallel_preview", { selected_country_ids: selectedCountryIds, target_type: targetType, target_id: targetId }, databasePath);
  if (!result.ok) throw new Error(result.error || "PARALLEL_PREVIEW_UNAVAILABLE");
  return result;
}

export function getParallelLeagueSnapshot(seasonNumber = 1, databasePath?: string) {
  return staffMarketAction<GatewayResult & ParallelLeagueSnapshot>("parallel_snapshot", { season_number: seasonNumber }, databasePath);
}

export function recordParallelLeagueResult(fixtureId: number, homeGoals: number, awayGoals: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { fixture_id: number; status: string; home_goals: number; away_goals: number }>("parallel_result", { fixture_id: fixtureId, home_goals: homeGoals, away_goals: awayGoals }, databasePath);
}

export function closeParallelLeagueSeason(seasonNumber = 1, databasePath?: string) {
  return staffMarketAction<GatewayResult & { status: string; season_number: number; next_season?: number; promoted_count: number; relegated_count: number; moves?: Array<Record<string, unknown>> }>("parallel_close", { season_number: seasonNumber }, databasePath);
}

export function startCareer(input: {
  managerName: string;
  nationality?: string;
  age: number;
  careerName: string;
  targetType: CareerTargetType;
  targetId: number;
  selectedCountryIds?: number[];
}, databasePath?: string) {
  const result = callGateway<GatewayResult & { started?: boolean }>("start", {
    manager_name: input.managerName,
    nationality: input.nationality || null,
    age: input.age,
    career_name: input.careerName,
    target_type: input.targetType,
    target_id: input.targetId,
    selected_country_ids: input.selectedCountryIds,
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

export function approvePlayerContractRenewal(input: { playerId: number; season: number; week: number; weeklySalary: number; durationWeeks?: number; signingFee?: number; bonus?: number; managerApproved: boolean; tickId?: string }, databasePath?: string) {
  return staffMarketAction<GatewayResult & { status: string; contract_id: number; player_id: number; club_id: number; weekly_salary: number; weekly_payroll: number; end_season: number; end_week: number }>("contract_renew_approve", { player_id: input.playerId, season: input.season, week: input.week, weekly_salary: input.weeklySalary, duration_weeks: input.durationWeeks ?? 52, signing_fee: input.signingFee ?? 0, bonus: input.bonus ?? 0, manager_approved: input.managerApproved, tick_id: input.tickId }, databasePath);
}

export function getClubFinanceRevenue(season?: number, databasePath?: string) { return staffMarketAction<GatewayResult & { items: unknown[] }>("finance_revenue", { season }, databasePath).items; }
export function getClubFinanceExpense(season?: number, databasePath?: string) { return staffMarketAction<GatewayResult & { items: unknown[] }>("finance_expense", { season }, databasePath).items; }
export function getClubFinanceBudget(projectedRevenue=0, projectedExpenses=0, databasePath?: string) { return staffMarketAction<GatewayResult & { budget: Record<string, unknown> }>("finance_budget", { projected_revenue: projectedRevenue, projected_expenses: projectedExpenses }, databasePath).budget; }
export function previewFinanceExpense(amount: number, category = "OTHER", databasePath?: string) { return staffMarketAction<GatewayResult & Record<string, unknown>>("finance_expense_preview", { amount, category }, databasePath); }
export function previewPostMatchFinance(matchdayRevenue: number, matchdayExpense: number, databasePath?: string) { return staffMarketAction<GatewayResult & Record<string, unknown>>("finance_post_match_preview", { matchday_revenue: matchdayRevenue, matchday_expense: matchdayExpense }, databasePath); }
export function getClubFinanceProjection(weeklyRevenue=0, weeklyExpenses=0, databasePath?: string) { return staffMarketAction<GatewayResult & Record<string, unknown>>("finance_projection", { weekly_revenue: weeklyRevenue, weekly_expenses: weeklyExpenses }, databasePath); }
export function getClubFinanceAlert(thresholdWeeks=4, databasePath?: string) { return staffMarketAction<GatewayResult & Record<string, unknown>>("finance_alert", { threshold_weeks: thresholdWeeks }, databasePath); }
export function getClubFinanceAudit(season: number, databasePath?: string) { return staffMarketAction<GatewayResult & Record<string, unknown>>("finance_audit", { season }, databasePath); }
export function previewTravelCost(matchId: number, clubId?: number, databasePath?: string) { return staffMarketAction<GatewayResult & { status: string; match_id: number; club_id: number; opponent_id: number; route_type: string; cost: number; currency: string; reason: string | null; persisted: boolean }>("travel_preview", { match_id: matchId, club_id: clubId }, databasePath); }
export function getTravelSummary(season?: number, databasePath?: string) { return staffMarketAction<GatewayResult & { club_id: number; season: number | null; trips: number; total_cost: number; currency: string; source: string }>("travel_summary", { season }, databasePath); }

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

export function getAiDiagnosis(databasePath?: string) {
  return staffMarketAction<GatewayResult & { club_id: number; needs: string[]; unavailable: number; squad_size: number; cash: number; health: string; objectives: Array<Record<string, unknown>> }>("ai_diagnosis", {}, databasePath);
}

export function getAiHistory(databasePath?: string) {
  return staffMarketAction<GatewayResult & { items: Array<Record<string, unknown>> }>("ai_history", {}, databasePath).items;
}

export function runAiWeekly(seed?: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { idempotent: boolean; decisions: Record<string, unknown> }>("ai_weekly", { seed }, databasePath);
}

export function getAiLineup(seed?: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { valid: boolean; player_ids: number[]; formation?: string; lineup_id?: number }>("ai_lineup", { seed }, databasePath);
}

export function getAiTactic(seed?: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { decision: string }>("ai_tactic", { seed }, databasePath);
}

export function previewTransferImpact(value: number, salary = 0, commission = 0, accessoryCost = 0, databasePath?: string) {
  return staffMarketAction<GatewayResult & { buyer_club_id: number; transfer_value: number; commission: number; accessory_cost: number; upfront_total: number; cash_before: number; cash_after: number; weekly_salary_before: number; weekly_salary_after: number; cash_sufficient: boolean; formula_version: string }>("transfer_preview", { value, salary, commission, accessory_cost: accessoryCost }, databasePath);
}

export function listTransferablePlayers(databasePath?: string) {
  return staffMarketAction<GatewayResult & { items: Array<Record<string, unknown>> }>("transferable_players", {}, databasePath).items;
}

export function createTransferOffer(payload: Record<string, unknown>, databasePath?: string) {
  return staffMarketAction<GatewayResult & { offer_id: number }>("transfer_offer", payload, databasePath);
}

export function approveTransferOffer(offerId: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { status?: string }>("transfer_approve", { offer_id: offerId }, databasePath);
}

export function createTransferLoan(payload: Record<string, unknown>, databasePath?: string) {
  return staffMarketAction<GatewayResult & { loan_id: number }>("transfer_loan", payload, databasePath);
}

export function listHealth(severity?: string, maxDays?: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { items: Array<{ injury_id: number; player_name: string; injury_type: string; severity: string; estimated_days: number }> }>("health_list", { severity, max_days: maxDays }, databasePath).items;
}

export function listHealthAlerts(databasePath?: string) {
  return staffMarketAction<GatewayResult & { items: Array<Record<string, unknown>> }>("health_alerts", {}, databasePath).items;
}

export function registerInjury(playerId: number, injuryType: string, severity: string, season: number, week: number, seed?: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & Record<string, unknown>>("health_injury", { player_id: playerId, injury_type: injuryType, severity, season, week, seed }, databasePath);
}

export function recoverPlayers(days = 1, databasePath?: string) {
  return staffMarketAction<GatewayResult & { items: Array<Record<string, unknown>> }>("health_recover", { days }, databasePath).items;
}

export function registerSuspension(playerId: number, cards: number, redCard: boolean, season: number, week: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & Record<string, unknown>>("health_suspension", { player_id: playerId, cards, red_card: redCard, season, week }, databasePath);
}

export function getMoraleSummary(databasePath?: string) {
  return staffMarketAction<GatewayResult & { club_id: number; average: number; members: number; lowest: number; highest: number }>("morale_summary", {}, databasePath);
}

export function updateMoraleAfterMatch(result: "WIN" | "DRAW" | "LOSS", season: number, week: number, seed?: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { average: number; members: number }>("morale_match", { result, season, week, seed }, databasePath);
}

export function applyWeeklyTraining(season: number, week: number, planType: string, load: number, seed?: number, internationalMatches = 0, databasePath?: string) {
  return staffMarketAction<GatewayResult & { club_id: number; changes: Array<Record<string, unknown>> }>("weekly_training", { season, week, plan_type: planType, load, seed, international_matches: internationalMatches }, databasePath);
}

export function createOpponentPreparation(opponentId: number, season: number, week: number, focus: string, databasePath?: string) {
  return staffMarketAction<GatewayResult & { preparation_id: number; adherence: number }>("opponent_preparation", { opponent_id: opponentId, season, week, focus }, databasePath);
}

export function getWeeklyLoad(season: number, week: number, databasePath?: string) {
  return staffMarketAction<GatewayResult & { players: Array<Record<string, unknown>>; total_load: number }>("weekly_load", { season, week }, databasePath);
}

export function getFormRecommendations(databasePath?: string) {
  return staffMarketAction<GatewayResult & { items: Array<{ player_id: number; type: string; reason: string }> }>("form_recommendations", {}, databasePath).items;
}

export function listTrainingAlerts(databasePath?: string) {
  return staffMarketAction<GatewayResult & { items: Array<{ department: string; message: string }> }>("training_alerts", {}, databasePath).items;
}

export function listDepartmentOffers(databasePath?: string) {
  return staffMarketAction<GatewayResult & { items: Array<{ department: string; label: string; target_level: number; cost: number; maintenance: number; capacity: number }> }>("department_offers", {}, databasePath).items;
}

export type StadiumUpgradePreview = { club_id: number; component: string; from_level: number; target_level: number; cost: number; maintenance_before: number; maintenance_after: number; cash_before: number; cash_after: number; cash_sufficient: boolean; persisted: boolean; formula_version: string };
export function previewStadiumUpgrade(component: string, databasePath?: string) { return staffMarketAction<GatewayResult & StadiumUpgradePreview>("stadium_preview", { component }, databasePath); }
export function upgradeClubDepartment(department: string, databasePath?: string) {
  return staffMarketAction<GatewayResult & { department: string; label: string; target_level: number; cost: number; maintenance: number; capacity: number; status: "IN_PROGRESS" | "COMPLETED"; started_at: string; completion_at: string; duration_weeks: number }>("department_upgrade", { department }, databasePath);
}

export function upgradeStadiumComponent(component: string, databasePath?: string) {
  return staffMarketAction<GatewayResult & Record<string, unknown>>("stadium_upgrade", { component }, databasePath);
}

export type TicketPricePreview = { club_id: number; ticket_price: number; expected_attendance: number; expected_revenue: number; rejection_risk: number; persisted: boolean; formula_version: string };
export function previewTicketPrice(basePrice: number, importance = 50, visitorReputation = 30, databasePath?: string) { return staffMarketAction<GatewayResult & TicketPricePreview>("ticket_price_preview", { base_price: basePrice, importance, visitor_reputation: visitorReputation }, databasePath); }
export function getFanSegments(databasePath?: string) { return staffMarketAction<GatewayResult & { club_id: number; segments: { local: number; national: number; international: number }; source: string }>("fan_segments", {}, databasePath); }
export function getSocialTimeline(limit = 25, offset = 0, databasePath?: string) { return staffMarketAction<GatewayResult & { club_id: number; items: Array<Record<string, unknown>>; limit: number; offset: number; source: string }>("social_timeline", { limit, offset }, databasePath); }

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
  return staffMarketAction<GatewayResult & { status: string; season: number; week: number; matches: number; controlled_club_id: number | null; skipped_controlled_matches: number; match_details: Array<Record<string, unknown>> }>("weekly_advance", { seed }, databasePath);
}

export type MatchControlDecisions = {
  tactics?: { mentality: string; attackLane: string; passing: string; pressure: string; crossing: boolean };
  substitutions?: Array<{ playerOutId: number; playerInId: number }>;
  penalty_taker_id?: number;
  red_card_response?: { formation: string; mentality: string };
};

export function playControlledMatch(matchId: number, seed?: number, decisions?: MatchControlDecisions, databasePath?: string) {
  return staffMarketAction<GatewayResult & { status: string; match_id: number; controlled_club_id: number; home_club_id: number; away_club_id: number; home_goals: number; away_goals: number; seed: number | null; control_events: Array<{ minute: number; type: string; payload: unknown }> }>("play_controlled_match", { match_id: matchId, seed, decisions }, databasePath);
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
