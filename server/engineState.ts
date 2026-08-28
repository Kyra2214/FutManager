import { createRequire } from "node:module";

import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

type SQLiteStatement = {
  all: (...parameters: unknown[]) => unknown[];
  get: (...parameters: unknown[]) => unknown;
};

type SQLiteDatabase = {
  close: () => void;
  prepare: (statement: string) => SQLiteStatement;
};

type SQLiteDatabaseConstructor = new (
  path: string,
  options?: { readOnly?: boolean },
) => SQLiteDatabase;

const runtimeRequire = createRequire(import.meta.url);
const { DatabaseSync } = runtimeRequire(["node", "sqlite"].join(":")) as {
  DatabaseSync: SQLiteDatabaseConstructor;
};

const MODULE_ROOT = dirname(fileURLToPath(import.meta.url));
const DEFAULT_ENGINE_ROOT = resolve(MODULE_ROOT, "../engine");
const DEFAULT_ENGINE_STATE_PATH = resolve(DEFAULT_ENGINE_ROOT, "data/state/game.db");
const ENGINE_ASSET_URL_PREFIX = "/engine-assets/";

type SQLiteRow = Record<string, unknown>;

export type CompetitionSummary = {
  competitionId: number;
  name: string;
  type: string;
  format: string;
  status: string;
  seasonId: number;
  seasonYear: number | null;
  registeredClubs: number;
  scheduledFixtures: number;
  playedMatches: number;
  currentPhase: { phaseId: number; name: string; status: string } | null;
  tiebreakers: string[];
};

export type StandingRow = {
  position: number;
  clubId: number;
  clubName: string;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goalsFor: number;
  goalsAgainst: number;
  goalDifference: number;
  points: number;
  isControlledClub: boolean;
};

export type MatchCard = {
  key: string;
  matchId: number | null;
  fixtureId: number | null;
  round: number | null;
  scheduledAt: string;
  status: string;
  homeClub: { clubId: number; name: string };
  awayClub: { clubId: number; name: string };
  homeGoals: number | null;
  awayGoals: number | null;
  isPlayed: boolean;
};

export type PlayerSeasonTotal = {
  playerId: number;
  minutes: number;
  goals: number;
  assists: number;
  cards: number;
  appearances: number;
  averageRating: number | null;
};

export type PlayerStatsRead = {
  source: { mode: "LOCAL_READ_ONLY_SQLITE"; available: boolean; message: string; generatedAt: string };
  competitionId: number | null;
  matchIds: number[];
  players: PlayerSeasonTotal[];
};

export type MatchesDashboard = {
  filters: { competitionId: number | null; season: number | null; phaseId: number | null };
  source: {
    mode: "LOCAL_READ_ONLY_SQLITE";
    available: boolean;
    message: string;
    generatedAt: string;
  };
  controlledClub: { clubId: number; name: string } | null;
  competitions: CompetitionSummary[];
  selectedCompetitionId: number | null;
  selectedCompetition: CompetitionSummary | null;
  standings: StandingRow[];
  upcomingFixtures: MatchCard[];
  recentResults: MatchCard[];
};

export type ClassificationPreview = { competitionId: number; homeClubId: number; awayClubId: number; homeGoals: number; awayGoals: number; standings: StandingRow[]; persisted: false; formulaVersion: string };
export type CompetitionComparison = { competitions: Array<{ competitionId: number; name: string; seasonYear: number | null; leader: StandingRow | null; clubs: number; played: number; pointsTotal: number }>; source: { mode: "LOCAL_READ_ONLY_SQLITE"; available: boolean; message: string; generatedAt: string } };

export type ContractRenewalPreview = { playerId: number; clubId: number; currentWeeklySalary: number; proposedWeeklySalary: number; weeklyDelta: number; currentClubPayroll: number | null; projectedClubPayroll: number | null; persisted: false; formulaVersion: string };

export type PlayerContractRead = { playerId: number; playerName: string; clubId: number | null; startSeason: number; startWeek: number; endSeason: number | null; endWeek: number | null; weeklySalary: number; releaseClause: number | null; status: string; source: string; weeksRemaining: number | null };
export type PlayerProfileRead = { playerId: number; playerName: string; clubId: number | null; position: string | null; status: string | null; form: number | null; condition: number | null; fatigue: number | null; available: boolean | null; activeInjury: { injuryId: number; type: string; severity: string; estimatedDays: number | null; endDate: string | null } | null; seasonTotals: PlayerSeasonTotal | null; contract: PlayerContractRead | null; source: { mode: "LOCAL_READ_ONLY_SQLITE"; available: boolean; message: string; generatedAt: string } };
export type PlayerEvolutionRead = { playerId: number; season: number | null; potential: number | null; currentStrength: number | null; performance: { minutes: number; goals: number; assists: number; appearances: number; averageRating: number | null } | null; gapToPotential: number | null; source: { mode: "LOCAL_READ_ONLY_SQLITE"; available: boolean; message: string; generatedAt: string } };

export type CompetitionHistoryRead = {
  competitionId: number;
  champions: Array<{ seasonId: number; clubId: number; clubName: string; finalizedAt: string }>;
  prizes: Array<{ position: number; amount: number }>;
  alerts: Array<{ alertId: number; seasonId: number; clubId: number; type: string; message: string; createdAt: string }>;
  source: { mode: "LOCAL_READ_ONLY_SQLITE"; available: boolean; message: string; generatedAt: string };
};

export type EntityAssetLink = {
  source: { available: boolean; message: string };
  entityType: "team" | "selection";
  entityId: number;
  entityName: string | null;
  mappingStatus: "COMPLETE" | "FULL_ONLY" | "MINI_ONLY" | "NO_SOURCE_ASSET" | "SOURCE_NOT_PROVIDED" | "ENTITY_NOT_FOUND" | "STATE_UNAVAILABLE";
  crestPath: string | null;
  crestUrl: string | null;
  miniCrestPath: string | null;
  miniCrestUrl: string | null;
  primaryKitPath: string | null;
  primaryKitUrl: string | null;
};

export type ClubWorkspaceDashboard = {
  source: { mode: "LOCAL_READ_ONLY_SQLITE"; available: boolean; message: string; generatedAt: string };
  career: { managerName: string; careerName: string; targetType: "club" | "selection"; targetId: number; targetName: string } | null;
  club: { clubId: number; name: string; stadiumName: string | null } | null;
  squad: { total: number; starters: number; reserves: number; injured: number; players: Array<{ playerId: number; name: string; age: number; position: string; status: string; category: string; cr1: number; cr2: number; side: string | null; star: boolean; topWorld: boolean }> };
  finance: {
    cash: number | null;
    updatedAt: string | null;
    source: "ECONOMIC_PROFILE" | "LEGACY_FINANCE" | "UNAVAILABLE";
    budget: number | null;
    initialCash: number | null;
    weeklyPlayerPayroll: number | null;
    weeklyStaffPayroll: number | null;
    weeklyDepartmentMaintenance: number | null;
    weeklyTotal: number | null;
    teamPower: number | null;
    countryFactor: number | null;
    baseLevel: number | null;
    ledgerIncome: number | null;
    ledgerExpense: number | null;
    projectedCash39Weeks: number | null;
    sponsorshipIncome: number | null;
    ticketIncome: number | null;
    prizeIncome: number | null;
  };
  reputation: { sporting: number | null; national: number | null; international: number | null; commercial: number | null; historical: number | null };
  stadium: { name: string | null; capacity: number | null; level: number | null; status: string | null; source: "CLUB_STADIUM" | "TEAM_RECORD" | "UNAVAILABLE" };
  training: { available: boolean; message: string };
  staff: { members: Array<{ staffId: number; name: string; role: string; age: number; experience: number; reputation: number; level: number; specialization: string | null; status: string }>; departments: Array<{ department: string; level: number; capacity: number; efficiency: number }>; roleCounts: Record<string, number>; averageLevel: number; history: Array<{ historyId: number; staffId: number; eventType: string; eventDate: string; payload: Record<string, unknown> }>; effects: Record<string, { effect: string; members: number; averageLevel: number; bonus: number }>; departmentCapacity: Array<{ department: string; capacity: number; used: number; vacancies: number; role: string | null }>; commissionBonus: number };
  health: { activeInjuries: Array<{ injuryId: number; playerId: number; playerName: string; injuryType: string; severity: string; estimatedDays: number | null; endDate: string | null }>; count: number };
  scouting: { missions: Array<{ missionId: number; scoutName: string | null; status: string; region: string | null; endDate: string; opportunities: number }>; opportunities: number; reports: number };
};

function asNumber(value: unknown, fallback = 0): number {
  if (typeof value === "number") return value;
  if (typeof value === "bigint") return Number(value);
  if (typeof value === "string" && value.trim() !== "") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }
  return fallback;
}

function asNullableNumber(value: unknown): number | null {
  return value === null || value === undefined ? null : asNumber(value);
}

function asText(value: unknown, fallback = "—"): string {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function tableExists(db: SQLiteDatabase, table: string) {
  return Boolean(db.prepare("SELECT 1 AS present FROM sqlite_master WHERE type = 'table' AND name = ? LIMIT 1").get(table));
}

function publicAssetUrl(relativePath: string | null): string | null {
  if (!relativePath || relativePath.includes("..") || !relativePath.startsWith("assets/")) return null;
  const encodedPath = relativePath.slice("assets/".length).split("/").map(encodeURIComponent).join("/");
  return `${ENGINE_ASSET_URL_PREFIX}${encodedPath}`;
}

function unavailableEntityAsset(entityType: EntityAssetLink["entityType"], entityId: number, message: string): EntityAssetLink {
  return {
    source: { available: false, message },
    entityType,
    entityId,
    entityName: null,
    mappingStatus: "STATE_UNAVAILABLE",
    crestPath: null,
    crestUrl: null,
    miniCrestPath: null,
    miniCrestUrl: null,
    primaryKitPath: null,
    primaryKitUrl: null,
  };
}

function emptyDashboard(message: string): MatchesDashboard {
  return {
    filters: { competitionId: null, season: null, phaseId: null },
    source: {
      mode: "LOCAL_READ_ONLY_SQLITE",
      available: false,
      message,
      generatedAt: new Date().toISOString(),
    },
    controlledClub: null,
    competitions: [],
    selectedCompetitionId: null,
    selectedCompetition: null,
    standings: [],
    upcomingFixtures: [],
    recentResults: [],
  };
}

function toCompetition(row: SQLiteRow): CompetitionSummary {
  return {
    competitionId: asNumber(row.competition_id),
    name: asText(row.name),
    type: asText(row.type),
    format: asText(row.format),
    status: asText(row.status),
    seasonId: asNumber(row.season_id),
    seasonYear: asNullableNumber(row.season_year),
    registeredClubs: asNumber(row.registered_clubs),
    scheduledFixtures: asNumber(row.scheduled_fixtures),
    playedMatches: asNumber(row.played_matches),
    currentPhase: row.current_phase_id === null || row.current_phase_id === undefined ? null : { phaseId: asNumber(row.current_phase_id), name: asText(row.current_phase_name), status: asText(row.current_phase_status) },
    tiebreakers: asText(row.tiebreakers, "points,wins,goal_difference,goals_for").split(",").map((item) => item.trim()).filter(Boolean),
  };
}

function toMatchCard(row: SQLiteRow): MatchCard {
  const status = asText(row.status, "SCHEDULED");
  const homeGoals = asNullableNumber(row.home_goals);
  const awayGoals = asNullableNumber(row.away_goals);
  const matchId = asNullableNumber(row.match_id);
  const fixtureId = asNullableNumber(row.fixture_id);

  return {
    key: matchId ? `match-${matchId}` : `fixture-${fixtureId}`,
    matchId,
    fixtureId,
    round: asNullableNumber(row.round_number),
    scheduledAt: asText(row.scheduled_at),
    status,
    homeClub: { clubId: asNumber(row.home_club_id), name: asText(row.home_club_name) },
    awayClub: { clubId: asNumber(row.away_club_id), name: asText(row.away_club_name) },
    homeGoals,
    awayGoals,
    isPlayed: status === "PLAYED" && homeGoals !== null && awayGoals !== null,
  };
}

function getControlledClub(db: SQLiteDatabase): MatchesDashboard["controlledClub"] {
  const row = db
    .prepare(
      `SELECT career.current_club_id AS club_id, teams.nome AS club_name
       FROM manager_careers career
       LEFT JOIN times teams ON teams.time_id = career.current_club_id
       WHERE career.status = 'ACTIVE' AND career.current_club_id IS NOT NULL
       ORDER BY career.updated_at DESC, career.career_id DESC
       LIMIT 1`,
    )
    .get() as SQLiteRow | undefined;

  if (!row || row.club_id === null || row.club_id === undefined) return null;

  return {
    clubId: asNumber(row.club_id),
    name: asText(row.club_name, "Clube controlado"),
  };
}

const PARALLEL_COMPETITION_ID_BASE = 900_000_000;

function getParallelCareerId(competitionId: number) {
  return competitionId - PARALLEL_COMPETITION_ID_BASE;
}

function getParallelCompetitionRows(db: SQLiteDatabase, season?: number): CompetitionSummary[] {
  if (!tableExists(db, "career_parallel_leagues")) return [];
  const activeCareer = tableExists(db, "manager_careers")
    ? db.prepare("SELECT career_id FROM manager_careers WHERE status='ACTIVE' ORDER BY updated_at DESC, career_id DESC LIMIT 1").get() as SQLiteRow | undefined
    : undefined;
  const careerId = activeCareer ? asNumber(activeCareer.career_id) : null;
  const rows = db.prepare(`SELECT league.career_id, league.name, league.season_id, league.total_clubs, league.division_count, league.created_at, (SELECT COUNT(*) FROM career_parallel_fixtures fixture WHERE fixture.career_id=league.career_id AND fixture.season_number=1 AND fixture.status='SCHEDULED') AS scheduled_fixtures, (SELECT COUNT(*) FROM career_parallel_fixtures fixture WHERE fixture.career_id=league.career_id AND fixture.season_number=1 AND fixture.status='PLAYED') AS played_matches FROM career_parallel_leagues league WHERE (? IS NULL OR league.career_id=?) ORDER BY league.career_id DESC`).all(careerId, careerId) as SQLiteRow[];
  return rows.filter((row) => season === undefined || season === null || season >= 2026).map((row) => ({
    competitionId: PARALLEL_COMPETITION_ID_BASE + asNumber(row.career_id),
    name: asText(row.name, "Liga da carreira"), type: "CAREER_PARALLEL", format: `${asNumber(row.division_count, 4)} divisões`, status: "ACTIVE",
    seasonId: asNumber(row.season_id, 1), seasonYear: 2026 + Math.max(0, asNumber(row.season_id, 1) - 1), registeredClubs: asNumber(row.total_clubs), scheduledFixtures: asNumber(row.scheduled_fixtures), playedMatches: asNumber(row.played_matches), currentPhase: null, tiebreakers: ["points", "wins", "goal_difference", "goals_for"],
  }));
}

function getCompetitionRows(db: SQLiteDatabase, season?: number): CompetitionSummary[] {
  if (!tableExists(db, "competitions")) return getParallelCompetitionRows(db, season);
  const rows = db
    .prepare(
      `SELECT
         competition.competition_id,
         competition.name,
         competition.type,
         competition.format,
         competition.status,
         competition.season_id,
         season.year AS season_year,
         (SELECT COUNT(*) FROM competition_entries entry WHERE entry.competition_id = competition.competition_id) AS registered_clubs,
         (SELECT COUNT(*) FROM fixtures fixture WHERE fixture.competition_id = competition.competition_id AND fixture.status = 'SCHEDULED') AS scheduled_fixtures,
         (SELECT COUNT(*) FROM matches game WHERE game.competition_id = competition.competition_id AND game.status = 'PLAYED') AS played_matches,
         config.tiebreakers,
         (SELECT phase_id FROM competition_phases phase WHERE phase.competition_id = competition.competition_id ORDER BY phase.order_no ASC, phase.phase_id ASC LIMIT 1) AS current_phase_id,
         (SELECT name FROM competition_phases phase WHERE phase.competition_id = competition.competition_id ORDER BY phase.order_no ASC, phase.phase_id ASC LIMIT 1) AS current_phase_name,
         (SELECT status FROM competition_phases phase WHERE phase.competition_id = competition.competition_id ORDER BY phase.order_no ASC, phase.phase_id ASC LIMIT 1) AS current_phase_status
       FROM competitions competition
       LEFT JOIN competition_config config ON config.competition_id = competition.competition_id
       LEFT JOIN seasons season ON season.season_id = competition.season_id
       WHERE (? IS NULL OR season.year = ?)
       ORDER BY
         CASE competition.status WHEN 'ACTIVE' THEN 0 WHEN 'PLANNED' THEN 1 ELSE 2 END,
         season.year DESC,
         competition.competition_id DESC`,
    )
    .all(season ?? null, season ?? null) as SQLiteRow[];

  const competitions = rows.map(toCompetition);
  return competitions.length ? competitions : getParallelCompetitionRows(db, season);
}

function getParallelStandings(db: SQLiteDatabase, competitionId: number, controlledClubId: number | null): StandingRow[] {
  const careerId = getParallelCareerId(competitionId);
  if (!tableExists(db, "career_parallel_standings")) return [];
  const rows = db.prepare("SELECT standings.*, teams.nome AS club_name FROM career_parallel_standings standings LEFT JOIN times teams ON teams.time_id=standings.club_id WHERE standings.career_id=? AND standings.season_number=1 ORDER BY standings.division, standings.position").all(careerId) as SQLiteRow[];
  return rows.map((row, index) => ({ position: index + 1, clubId: asNumber(row.club_id), clubName: asText(row.club_name, `Clube #${asNumber(row.club_id)}`), played: asNumber(row.played), wins: asNumber(row.wins), draws: asNumber(row.draws), losses: asNumber(row.losses), goalsFor: asNumber(row.goals_for), goalsAgainst: asNumber(row.goals_against), goalDifference: asNumber(row.goals_for) - asNumber(row.goals_against), points: asNumber(row.points), isControlledClub: asNumber(row.club_id) === controlledClubId }));
}

function getStandings(db: SQLiteDatabase, competitionId: number, controlledClubId: number | null): StandingRow[] {
  const rows = db
    .prepare(
      `SELECT
         stats.club_id,
         teams.nome AS club_name,
         stats.played,
         stats.wins,
         stats.draws,
         stats.losses,
         stats.goals_for,
         stats.goals_against,
         stats.points,
         (stats.goals_for - stats.goals_against) AS goal_difference
       FROM team_competition_stats stats
       INNER JOIN times teams ON teams.time_id = stats.club_id
       WHERE stats.competition_id = ?
       ORDER BY stats.points DESC, stats.wins DESC, goal_difference DESC, stats.goals_for DESC, teams.nome ASC`,
    )
    .all(competitionId) as SQLiteRow[];

  return rows.map((row, index) => ({
    position: index + 1,
    clubId: asNumber(row.club_id),
    clubName: asText(row.club_name),
    played: asNumber(row.played),
    wins: asNumber(row.wins),
    draws: asNumber(row.draws),
    losses: asNumber(row.losses),
    goalsFor: asNumber(row.goals_for),
    goalsAgainst: asNumber(row.goals_against),
    goalDifference: asNumber(row.goal_difference),
    points: asNumber(row.points),
    isControlledClub: asNumber(row.club_id) === controlledClubId,
  }));
}

function getParallelMatches(db: SQLiteDatabase, competitionId: number): MatchCard[] {
  const careerId = getParallelCareerId(competitionId);
  if (!tableExists(db, "career_parallel_fixtures")) return [];
  const rows = db.prepare("SELECT fixture_id, scheduled_date AS scheduled_at, status, matchday AS round_number, home_club_id, away_club_id, home_goals, away_goals FROM career_parallel_fixtures WHERE career_id=? AND season_number=1 ORDER BY scheduled_date, matchday, fixture_id").all(careerId) as SQLiteRow[];
  const names = new Map<number, string>();
  if (tableExists(db, "times")) for (const row of db.prepare("SELECT time_id,nome FROM times").all() as SQLiteRow[]) names.set(asNumber(row.time_id), asText(row.nome, `Clube #${asNumber(row.time_id)}`));
  return rows.map((row) => toMatchCard({ ...row, home_club_name: names.get(asNumber(row.home_club_id)), away_club_name: names.get(asNumber(row.away_club_id)), match_id: null }));
}

function getMatches(db: SQLiteDatabase, competitionId: number, phaseId?: number): MatchCard[] {
  const rows = db
    .prepare(
      `SELECT
         fixture.fixture_id,
         fixture.match_id,
         fixture.scheduled_at,
         COALESCE(game.status, fixture.status) AS status,
         round.number AS round_number,
         fixture.home_club_id,
         home.nome AS home_club_name,
         fixture.away_club_id,
         away.nome AS away_club_name,
         game.home_goals,
         game.away_goals
       FROM fixtures fixture
       LEFT JOIN matches game ON game.match_id = fixture.match_id
       LEFT JOIN competition_rounds round ON round.round_id = fixture.round_id
       INNER JOIN times home ON home.time_id = fixture.home_club_id
       INNER JOIN times away ON away.time_id = fixture.away_club_id
       WHERE fixture.competition_id = ?
         AND (? IS NULL OR fixture.round_id IN (SELECT round_id FROM competition_rounds WHERE phase_id = ?))
       UNION ALL
       SELECT
         NULL AS fixture_id,
         game.match_id,
         game.match_date AS scheduled_at,
         game.status,
         game.round AS round_number,
         game.home_club_id,
         home.nome AS home_club_name,
         game.away_club_id,
         away.nome AS away_club_name,
         game.home_goals,
         game.away_goals
       FROM matches game
       INNER JOIN times home ON home.time_id = game.home_club_id
       INNER JOIN times away ON away.time_id = game.away_club_id
       WHERE game.competition_id = ?
         AND (? IS NULL OR game.round IN (SELECT number FROM competition_rounds WHERE phase_id = ?))
         AND NOT EXISTS (SELECT 1 FROM fixtures fixture WHERE fixture.match_id = game.match_id)
       ORDER BY scheduled_at ASC, round_number ASC`,
    )
    .all(competitionId, phaseId ?? null, phaseId ?? null, competitionId, phaseId ?? null, phaseId ?? null) as SQLiteRow[];

  return rows.map(toMatchCard);
}

export function getPlayerSeasonTotals(
  competitionId?: number,
  matchIds?: number[],
  databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH,
): PlayerStatsRead {
  const generatedAt = new Date().toISOString();
  let db: SQLiteDatabase | null = null;
  try {
    db = new DatabaseSync(databasePath, { readOnly: true });
    if (!tableExists(db, "player_match_stats")) {
      return { source: { mode: "LOCAL_READ_ONLY_SQLITE", available: true, message: "O estado está conectado, mas não há estatísticas individuais persistidas.", generatedAt }, competitionId: competitionId ?? null, matchIds: matchIds ?? [], players: [] };
    }
    const clauses: string[] = [];
    const params: unknown[] = [];
    if (matchIds?.length) { clauses.push(`stats.match_id IN (${matchIds.map(() => "?").join(",")})`); params.push(...matchIds); }
    if (competitionId !== undefined) { clauses.push("EXISTS (SELECT 1 FROM matches m WHERE m.match_id=stats.match_id AND m.competition_id=?)"); params.push(competitionId); }
    const rows = db.prepare(`SELECT stats.player_id,SUM(stats.minutes) AS minutes,SUM(stats.goals) AS goals,SUM(stats.assists) AS assists,SUM(stats.cards) AS cards,COUNT(*) AS appearances,AVG(stats.rating) AS average_rating FROM player_match_stats stats${clauses.length ? ` WHERE ${clauses.join(" AND ")}` : ""} GROUP BY stats.player_id ORDER BY goals DESC,assists DESC,minutes DESC,stats.player_id`).all(...params) as SQLiteRow[];
    return { source: { mode: "LOCAL_READ_ONLY_SQLITE", available: true, message: "Agregados individuais lidos diretamente do GameState em modo somente leitura.", generatedAt }, competitionId: competitionId ?? null, matchIds: matchIds ?? [], players: rows.map((row) => ({ playerId: asNumber(row.player_id), minutes: asNumber(row.minutes), goals: asNumber(row.goals), assists: asNumber(row.assists), cards: asNumber(row.cards), appearances: asNumber(row.appearances), averageRating: asNullableNumber(row.average_rating) })) };
  } catch (error) {
    console.error("[Player stats] Falha ao consultar estatísticas individuais:", error);
    return { source: { mode: "LOCAL_READ_ONLY_SQLITE", available: false, message: "O estado local do motor não está disponível para leitura de estatísticas.", generatedAt }, competitionId: competitionId ?? null, matchIds: matchIds ?? [], players: [] };
  } finally { db?.close(); }
}

export function getMatchesDashboard(competitionId?: number, databasePath?: string): MatchesDashboard;
export function getMatchesDashboard(competitionId?: number, season?: number, phaseId?: number, databasePath?: string): MatchesDashboard;
export function getMatchesDashboard(
  competitionId?: number,
  seasonOrDatabasePath?: number | string,
  phaseOrDatabasePath?: number | string,
  configuredDatabasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH,
): MatchesDashboard {
  const legacyDatabasePath = typeof seasonOrDatabasePath === "string" ? seasonOrDatabasePath : undefined;
  const season = typeof seasonOrDatabasePath === "number" ? seasonOrDatabasePath : undefined;
  const phaseId = typeof phaseOrDatabasePath === "number" ? phaseOrDatabasePath : undefined;
  const databasePath = typeof phaseOrDatabasePath === "string" ? phaseOrDatabasePath : legacyDatabasePath ?? configuredDatabasePath;
  let db: SQLiteDatabase | null = null;

  try {
    db = new DatabaseSync(databasePath, { readOnly: true });
    const controlledClub = getControlledClub(db);
    const competitions = getCompetitionRows(db, season);
    const selectedCompetition =
      competitions.find((competition) => competition.competitionId === competitionId) ?? competitions[0] ?? null;

    if (!selectedCompetition) {
      return {
        ...emptyDashboard("O motor está conectado, mas ainda não há competições persistidas na carreira."),
        filters: { competitionId: competitionId ?? null, season: season ?? null, phaseId: phaseId ?? null },
        source: {
          mode: "LOCAL_READ_ONLY_SQLITE",
          available: true,
          message: "O motor está conectado, mas ainda não há competições persistidas na carreira.",
          generatedAt: new Date().toISOString(),
        },
        controlledClub,
      };
    }

    const isParallelCompetition = selectedCompetition.competitionId >= PARALLEL_COMPETITION_ID_BASE;
    const allMatches = isParallelCompetition ? getParallelMatches(db, selectedCompetition.competitionId) : getMatches(db, selectedCompetition.competitionId, phaseId);
    return {
      filters: { competitionId: selectedCompetition.competitionId, season: season ?? selectedCompetition.seasonYear ?? null, phaseId: phaseId ?? null },
      source: {
        mode: "LOCAL_READ_ONLY_SQLITE",
        available: true,
        message: "Consulta direta ao estado SQLite do motor em modo somente leitura.",
        generatedAt: new Date().toISOString(),
      },
      controlledClub,
      competitions,
      selectedCompetitionId: selectedCompetition.competitionId,
      selectedCompetition,
      standings: isParallelCompetition ? getParallelStandings(db, selectedCompetition.competitionId, controlledClub?.clubId ?? null) : getStandings(db, selectedCompetition.competitionId, controlledClub?.clubId ?? null),
      upcomingFixtures: allMatches.filter((match) => !match.isPlayed),
      recentResults: allMatches.filter((match) => match.isPlayed).reverse(),
    };
  } catch (error) {
    console.error("[Engine state] Falha ao consultar o estado SQLite em modo somente leitura:", error);
    return { ...emptyDashboard("O estado local do motor não está disponível para leitura neste ambiente."), filters: { competitionId: competitionId ?? null, season: season ?? null, phaseId: phaseId ?? null } };
  } finally {
    db?.close();
  }
}

export function previewContractRenewal(playerId: number, clubId: number, proposedWeeklySalary: number, databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH): ContractRenewalPreview {
  if (proposedWeeklySalary < 0) throw new Error("INVALID_WEEKLY_SALARY");
  let db: SQLiteDatabase | null = null;
  try {
    db = new DatabaseSync(databasePath, { readOnly: true });
    if (!tableExists(db, "player_contract_history")) throw new Error("CONTRACT_HISTORY_UNAVAILABLE");
    const contract = db.prepare("SELECT weekly_salary FROM player_contract_history WHERE player_id=? AND club_id=? AND status IN ('ACTIVE','ATIVO','active') ORDER BY contract_id DESC LIMIT 1").get(playerId, clubId) as SQLiteRow | undefined;
    if (!contract) throw new Error("ACTIVE_CONTRACT_NOT_FOUND");
    const payroll = tableExists(db, "club_payroll_profiles") ? (db.prepare("SELECT weekly_player_payroll FROM club_payroll_profiles WHERE club_id=?").get(clubId) as SQLiteRow | undefined) : undefined;
    const currentWeeklySalary = asNumber(contract.weekly_salary); const weeklyDelta = proposedWeeklySalary - currentWeeklySalary; const currentClubPayroll = payroll ? asNullableNumber(payroll.weekly_player_payroll) : null;
    return { playerId, clubId, currentWeeklySalary, proposedWeeklySalary, weeklyDelta, currentClubPayroll, projectedClubPayroll: currentClubPayroll === null ? null : currentClubPayroll + weeklyDelta, persisted: false, formulaVersion: "contract-renewal-impact-v1" };
  } finally { db?.close(); }
}

export function getPlayerContracts(clubId: number, season?: number, week = 1, withinWeeks = 8, databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH): { clubId: number; contracts: PlayerContractRead[]; source: { mode: "LOCAL_READ_ONLY_SQLITE"; available: boolean; message: string; generatedAt: string } } {
  const generatedAt = new Date().toISOString(); let db: SQLiteDatabase | null = null;
  try {
    db = new DatabaseSync(databasePath, { readOnly: true });
    if (!tableExists(db, "player_contract_history")) return { clubId, contracts: [], source: { mode: "LOCAL_READ_ONLY_SQLITE", available: true, message: "O histórico de contratos ainda não está persistido para este estado.", generatedAt } };
    const rows = db.prepare(`SELECT history.player_id, players.nome AS player_name, history.club_id, history.start_season, history.start_week, history.end_season, history.end_week, history.weekly_salary, history.release_clause, history.status, history.source FROM player_contract_history history LEFT JOIN jogadores players ON players.jogador_id = history.player_id WHERE history.club_id = ? AND history.status IN ('ACTIVE','ATIVO','active') ORDER BY history.end_season IS NULL, history.end_season, history.end_week, players.nome`).all(clubId) as SQLiteRow[];
    const currentSeason = season ?? 0; const currentWeek = Math.max(1, week); const horizon = Math.max(0, withinWeeks);
    return { clubId, contracts: rows.map((row) => { const endSeason = asNullableNumber(row.end_season); const endWeek = asNullableNumber(row.end_week); const weeksRemaining = endSeason === null || endWeek === null || season === undefined ? null : (endSeason - currentSeason) * 52 + endWeek - currentWeek; return { playerId: asNumber(row.player_id), playerName: asText(row.player_name, `Jogador ${asNumber(row.player_id)}`), clubId: asNullableNumber(row.club_id), startSeason: asNumber(row.start_season), startWeek: asNumber(row.start_week), endSeason, endWeek, weeklySalary: asNumber(row.weekly_salary), releaseClause: asNullableNumber(row.release_clause), status: asText(row.status), source: asText(row.source), weeksRemaining }; }).filter((contract) => contract.weeksRemaining === null || contract.weeksRemaining <= horizon) , source: { mode: "LOCAL_READ_ONLY_SQLITE", available: true, message: "Contratos ativos lidos diretamente do histórico canônico do GameState.", generatedAt } };
  } catch (error) { console.error("[Player contracts] Falha ao consultar:", error); return { clubId, contracts: [], source: { mode: "LOCAL_READ_ONLY_SQLITE", available: false, message: "Os contratos do elenco não estão disponíveis para leitura.", generatedAt } }; } finally { db?.close(); }
}

export function getPlayerProfile(playerId: number, season?: number, databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH): PlayerProfileRead {
  const generatedAt = new Date().toISOString(); let db: SQLiteDatabase | null = null;
  try {
    db = new DatabaseSync(databasePath, { readOnly: true });
    const player = db.prepare("SELECT jogador_id, nome FROM jogadores WHERE jogador_id=?").get(playerId) as SQLiteRow | undefined;
    if (!player) throw new Error("PLAYER_NOT_FOUND");
    const sport = tableExists(db, "player_sport_state") ? db.prepare("SELECT club_id, condition, fatigue, form, available FROM player_sport_state WHERE player_id=? ORDER BY last_updated DESC LIMIT 1").get(playerId) as SQLiteRow | undefined : undefined;
    const position = tableExists(db, "player_positions") ? db.prepare("SELECT position_code FROM player_positions WHERE player_id=? ORDER BY updated_at DESC LIMIT 1").get(playerId) as SQLiteRow | undefined : undefined;
    const injury = tableExists(db, "injuries") ? db.prepare("SELECT injury_id, injury_type, severity, estimated_days, end_date FROM injuries WHERE player_id=? AND status IN ('ACTIVE','active','OPEN') ORDER BY injury_id DESC LIMIT 1").get(playerId) as SQLiteRow | undefined : undefined;
    const totals = tableExists(db, "player_match_stats") ? db.prepare("SELECT player_id,SUM(minutes) AS minutes,SUM(goals) AS goals,SUM(assists) AS assists,SUM(cards) AS cards,COUNT(*) AS appearances,AVG(rating) AS average_rating FROM player_match_stats WHERE player_id=? GROUP BY player_id").get(playerId) as SQLiteRow | undefined : undefined;
    const contract = tableExists(db, "player_contract_history") ? db.prepare("SELECT history.player_id, players.nome AS player_name, history.club_id, history.start_season, history.start_week, history.end_season, history.end_week, history.weekly_salary, history.release_clause, history.status, history.source FROM player_contract_history history LEFT JOIN jogadores players ON players.jogador_id=history.player_id WHERE history.player_id=? AND history.status IN ('ACTIVE','ATIVO','active') ORDER BY history.contract_id DESC LIMIT 1").get(playerId) as SQLiteRow | undefined : undefined;
    const seasonTotals = totals ? { playerId, minutes: asNumber(totals.minutes), goals: asNumber(totals.goals), assists: asNumber(totals.assists), cards: asNumber(totals.cards), appearances: asNumber(totals.appearances), averageRating: asNullableNumber(totals.average_rating) } : null;
    const contractRead = contract ? { playerId, playerName: asText(contract.player_name, asText(player.nome, `Jogador ${playerId}`)), clubId: asNullableNumber(contract.club_id), startSeason: asNumber(contract.start_season), startWeek: asNumber(contract.start_week), endSeason: asNullableNumber(contract.end_season), endWeek: asNullableNumber(contract.end_week), weeklySalary: asNumber(contract.weekly_salary), releaseClause: asNullableNumber(contract.release_clause), status: asText(contract.status), source: asText(contract.source), weeksRemaining: null } : null;
    return { playerId, playerName: asText(player.nome, `Jogador ${playerId}`), clubId: sport ? asNullableNumber(sport.club_id) : contractRead?.clubId ?? null, position: position ? asText(position.position_code, "") || null : null, status: sport && sport.available !== null && sport.available !== undefined ? Boolean(sport.available) ? "AVAILABLE" : "UNAVAILABLE" : null, form: sport ? asNullableNumber(sport.form) : null, condition: sport ? asNullableNumber(sport.condition) : null, fatigue: sport ? asNullableNumber(sport.fatigue) : null, available: sport ? Boolean(sport.available) : null, activeInjury: injury ? { injuryId: asNumber(injury.injury_id), type: asText(injury.injury_type), severity: asText(injury.severity), estimatedDays: asNullableNumber(injury.estimated_days), endDate: injury.end_date == null ? null : asText(injury.end_date) } : null, seasonTotals, contract: contractRead, source: { mode: "LOCAL_READ_ONLY_SQLITE", available: true, message: "Perfil do atleta lido diretamente do GameState em modo somente leitura.", generatedAt } };
  } catch (error) { console.error("[Player profile] Falha ao consultar:", error); return { playerId, playerName: `Jogador ${playerId}`, clubId: null, position: null, status: null, form: null, condition: null, fatigue: null, available: null, activeInjury: null, seasonTotals: null, contract: null, source: { mode: "LOCAL_READ_ONLY_SQLITE", available: false, message: "O perfil do atleta não está disponível para leitura.", generatedAt } }; } finally { db?.close(); }
}

export function comparePlayerEvolution(playerId: number, season?: number, databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH): PlayerEvolutionRead {
  const generatedAt = new Date().toISOString(); let db: SQLiteDatabase | null = null;
  try {
    db = new DatabaseSync(databasePath, { readOnly: true });
    const state = tableExists(db, "player_career_state") ? db.prepare("SELECT potential, current_strength FROM player_career_state WHERE player_id=? ORDER BY generation DESC LIMIT 1").get(playerId) as SQLiteRow | undefined : undefined;
    if (!state) throw new Error("PLAYER_CAREER_STATE_UNAVAILABLE");
    const params: unknown[] = [playerId]; let seasonClause = "";
    if (season !== undefined && tableExists(db, "matches") && tableExists(db, "seasons")) { seasonClause = " AND EXISTS (SELECT 1 FROM matches m INNER JOIN seasons s ON s.season_id=m.season_id WHERE m.match_id=stats.match_id AND s.year=?)"; params.push(season); }
    const stats = tableExists(db, "player_match_stats") ? db.prepare(`SELECT SUM(stats.minutes) AS minutes,SUM(stats.goals) AS goals,SUM(stats.assists) AS assists,COUNT(*) AS appearances,AVG(stats.rating) AS average_rating FROM player_match_stats stats WHERE stats.player_id=?${seasonClause}`).get(...params) as SQLiteRow | undefined : undefined;
    const currentStrength = asNullableNumber(state.current_strength); const potential = asNullableNumber(state.potential);
    const performance = stats && stats.appearances !== null ? { minutes: asNumber(stats.minutes), goals: asNumber(stats.goals), assists: asNumber(stats.assists), appearances: asNumber(stats.appearances), averageRating: asNullableNumber(stats.average_rating) } : null;
    return { playerId, season: season ?? null, potential, currentStrength, performance, gapToPotential: potential === null || currentStrength === null ? null : potential - currentStrength, source: { mode: "LOCAL_READ_ONLY_SQLITE", available: true, message: "Comparação de evolução derivada do GameState em modo somente leitura.", generatedAt } };
  } catch (error) { console.error("[Player evolution] Falha ao consultar:", error); return { playerId, season: season ?? null, potential: null, currentStrength: null, performance: null, gapToPotential: null, source: { mode: "LOCAL_READ_ONLY_SQLITE", available: false, message: "A evolução do atleta não está disponível para leitura.", generatedAt } }; } finally { db?.close(); }
}

export function previewClassification(competitionId: number, homeClubId: number, awayClubId: number, homeGoals: number, awayGoals: number, databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH): ClassificationPreview {
  if (homeGoals < 0 || awayGoals < 0) throw new Error("INVALID_SCORE");
  let db: SQLiteDatabase | null = null;
  try {
    db = new DatabaseSync(databasePath, { readOnly: true });
    const base = getStandings(db, competitionId, null).map((row) => ({ ...row }));
    const home = base.find((row) => row.clubId === homeClubId); const away = base.find((row) => row.clubId === awayClubId);
    if (!home || !away) throw new Error("CLASSIFICATION_CLUB_NOT_FOUND");
    const delta = homeGoals > awayGoals ? [3, 0] : homeGoals < awayGoals ? [0, 3] : [1, 1];
    for (const [row, goalsFor, goalsAgainst, points] of [[home, homeGoals, awayGoals, delta[0]], [away, awayGoals, homeGoals, delta[1]] ] as const) { row.played += 1; row.goalsFor += goalsFor; row.goalsAgainst += goalsAgainst; row.goalDifference = row.goalsFor - row.goalsAgainst; row.points += points; if (points === 3) row.wins += 1; else if (points === 1) row.draws += 1; else row.losses += 1; }
    base.sort((a, b) => b.points - a.points || b.wins - a.wins || b.goalDifference - a.goalDifference || b.goalsFor - a.goalsFor || a.clubName.localeCompare(b.clubName));
    return { competitionId, homeClubId, awayClubId, homeGoals, awayGoals, standings: base.map((row, index) => ({ ...row, position: index + 1 })), persisted: false, formulaVersion: "classification-preview-v1" };
  } finally { db?.close(); }
}

export function compareCompetitions(competitionIds: number[] | undefined, databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH): CompetitionComparison {
  let db: SQLiteDatabase | null = null; const generatedAt = new Date().toISOString();
  try { db = new DatabaseSync(databasePath, { readOnly: true }); const competitions = getCompetitionRows(db).filter((item) => !competitionIds?.length || competitionIds.includes(item.competitionId)); return { competitions: competitions.map((competition) => { const standings = getStandings(db!, competition.competitionId, null); return { competitionId: competition.competitionId, name: competition.name, seasonYear: competition.seasonYear, leader: standings[0] ?? null, clubs: standings.length, played: standings.reduce((total, row) => total + row.played, 0), pointsTotal: standings.reduce((total, row) => total + row.points, 0) }; }), source: { mode: "LOCAL_READ_ONLY_SQLITE", available: true, message: "Comparação de competições derivada do GameState em modo somente leitura.", generatedAt } }; } catch (error) { console.error("[Competition comparison] Falha ao consultar:", error); return { competitions: [], source: { mode: "LOCAL_READ_ONLY_SQLITE", available: false, message: "A comparação de competições não está disponível.", generatedAt } }; } finally { db?.close(); }
}

export function getCompetitionHistory(competitionId: number, databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH): CompetitionHistoryRead {
  let db: SQLiteDatabase | null = null;
  const generatedAt = new Date().toISOString();
  try {
    db = new DatabaseSync(databasePath, { readOnly: true });
    const champions = tableExists(db, "competition_champions") ? db.prepare(`SELECT champion.season_id, champion.champion_club_id, teams.nome AS club_name, champion.finalized_at FROM competition_champions champion LEFT JOIN times teams ON teams.time_id = champion.champion_club_id WHERE champion.competition_id = ? ORDER BY champion.season_id DESC`).all(competitionId) as SQLiteRow[] : [];
    const prizes = tableExists(db, "competition_prizes") ? db.prepare("SELECT position, amount FROM competition_prizes WHERE competition_id=? ORDER BY position").all(competitionId) as SQLiteRow[] : [];
    const alerts = tableExists(db, "classification_alerts") ? db.prepare("SELECT alert_id, season_id, club_id, alert_type, message, created_at FROM classification_alerts WHERE competition_id=? ORDER BY alert_id DESC LIMIT 50").all(competitionId) as SQLiteRow[] : [];
    return { competitionId, champions: champions.map((row) => ({ seasonId: asNumber(row.season_id), clubId: asNumber(row.champion_club_id), clubName: asText(row.club_name), finalizedAt: asText(row.finalized_at) })), prizes: prizes.map((row) => ({ position: asNumber(row.position), amount: asNumber(row.amount) })), alerts: alerts.map((row) => ({ alertId: asNumber(row.alert_id), seasonId: asNumber(row.season_id), clubId: asNumber(row.club_id), type: asText(row.alert_type), message: asText(row.message), createdAt: asText(row.created_at) })), source: { mode: "LOCAL_READ_ONLY_SQLITE", available: true, message: "Histórico canônico de competição lido em modo somente leitura.", generatedAt } };
  } catch (error) {
    console.error("[Competition history] Falha ao consultar histórico:", error);
    return { competitionId, champions: [], prizes: [], alerts: [], source: { mode: "LOCAL_READ_ONLY_SQLITE", available: false, message: "O histórico da competição não está disponível para leitura.", generatedAt } };
  } finally { db?.close(); }
}

export function getEntityAssetLink(
  entityType: EntityAssetLink["entityType"],
  entityId: number,
  databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH,
): EntityAssetLink {
  let db: SQLiteDatabase | null = null;

  try {
    db = new DatabaseSync(databasePath, { readOnly: true });
    const row = (entityType === "team"
      ? db.prepare(
          `SELECT team.time_id AS entity_id, team.nome AS entity_name, link.mapping_status,
                  crest.relative_path AS crest_path, mini.relative_path AS mini_crest_path,
                  NULL AS primary_kit_path
           FROM times team
           LEFT JOIN team_asset_links link ON link.time_id = team.time_id
           LEFT JOIN asset_catalog crest ON crest.asset_id = link.crest_asset_id
           LEFT JOIN asset_catalog mini ON mini.asset_id = link.crest_mini_asset_id
           WHERE team.time_id = ?`,
        )
      : db.prepare(
          `SELECT selection.selecao_id AS entity_id, selection.nome AS entity_name, link.crest_status AS mapping_status,
                  crest.relative_path AS crest_path, NULL AS mini_crest_path,
                  kit.relative_path AS primary_kit_path
           FROM selecoes selection
           LEFT JOIN selection_asset_links link ON link.selecao_id = selection.selecao_id
           LEFT JOIN asset_catalog crest ON crest.asset_id = link.crest_asset_id
           LEFT JOIN asset_catalog kit ON kit.asset_id = link.primary_kit_asset_id
           WHERE selection.selecao_id = ?`,
        )
    ).get(entityId) as SQLiteRow | undefined;

    if (!row) {
      return {
        ...unavailableEntityAsset(entityType, entityId, "A entidade solicitada não existe no estado do motor."),
        source: { available: true, message: "A entidade solicitada não existe no estado do motor." },
        mappingStatus: "ENTITY_NOT_FOUND",
      };
    }

    const crestPath = typeof row.crest_path === "string" ? row.crest_path : null;
    const miniCrestPath = typeof row.mini_crest_path === "string" ? row.mini_crest_path : null;
    const primaryKitPath = typeof row.primary_kit_path === "string" ? row.primary_kit_path : null;
    const mappingStatus = asText(row.mapping_status, entityType === "selection" ? "SOURCE_NOT_PROVIDED" : "NO_SOURCE_ASSET") as EntityAssetLink["mappingStatus"];

    return {
      source: { available: true, message: "Vínculo de ativo consultado diretamente no SQLite do motor." },
      entityType,
      entityId: asNumber(row.entity_id),
      entityName: typeof row.entity_name === "string" ? row.entity_name : null,
      mappingStatus,
      crestPath,
      crestUrl: publicAssetUrl(crestPath),
      miniCrestPath,
      miniCrestUrl: publicAssetUrl(miniCrestPath),
      primaryKitPath,
      primaryKitUrl: publicAssetUrl(primaryKitPath),
    };
  } catch (error) {
    console.error("[Engine assets] Falha ao consultar vínculo de ativo:", error);
    return unavailableEntityAsset(entityType, entityId, "O estado de ativos do motor não está disponível neste ambiente.");
  } finally {
    db?.close();
  }
}

function emptyClubWorkspace(message: string): ClubWorkspaceDashboard {
  return {
    source: { mode: "LOCAL_READ_ONLY_SQLITE", available: false, message, generatedAt: new Date().toISOString() },
    career: null,
    club: null,
    squad: { total: 0, starters: 0, reserves: 0, injured: 0, players: [] },
    finance: { cash: null, updatedAt: null, source: "UNAVAILABLE", budget: null, initialCash: null, weeklyPlayerPayroll: null, weeklyStaffPayroll: null, weeklyDepartmentMaintenance: null, weeklyTotal: null, teamPower: null, countryFactor: null, baseLevel: null, ledgerIncome: null, ledgerExpense: null, projectedCash39Weeks: null, sponsorshipIncome: null, ticketIncome: null, prizeIncome: null },
    reputation: { sporting: null, national: null, international: null, commercial: null, historical: null },
    stadium: { name: null, capacity: null, level: null, status: null, source: "UNAVAILABLE" },
    training: { available: false, message: "O estado do motor ainda não possui CT persistido para este clube." },
    staff: { members: [], departments: [], roleCounts: {}, averageLevel: 0, history: [], effects: {}, departmentCapacity: [], commissionBonus: 0 },
    health: { activeInjuries: [], count: 0 },
    scouting: { missions: [], opportunities: 0, reports: 0 },
  };
}

export function getClubWorkspaceDashboard(
  databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH,
): ClubWorkspaceDashboard {
  let db: SQLiteDatabase | null = null;
  try {
    db = new DatabaseSync(databasePath, { readOnly: true });
    const active = db.prepare(
      `SELECT career.career_id, career.name AS career_name, manager.name AS manager_name,
              career.current_club_id, team.nome AS club_name, team.estadio AS team_stadium,
              assignment.selection_id, selection.nome AS selection_name
       FROM manager_careers career
       INNER JOIN managers manager ON manager.manager_id = career.manager_id
       LEFT JOIN times team ON team.time_id = career.current_club_id
       LEFT JOIN manager_selection_assignments assignment ON assignment.career_id = career.career_id AND assignment.status = 'ACTIVE'
       LEFT JOIN selecoes selection ON selection.selecao_id = assignment.selection_id
       WHERE career.status = 'ACTIVE'
       ORDER BY career.updated_at DESC, career.career_id DESC
       LIMIT 1`,
    ).get() as SQLiteRow | undefined;
    if (!active) return { ...emptyClubWorkspace("O motor está conectado, mas a carreira ainda não foi iniciada."), source: { mode: "LOCAL_READ_ONLY_SQLITE", available: true, message: "O motor está conectado, mas a carreira ainda não foi iniciada.", generatedAt: new Date().toISOString() } };

    const selectionId = asNullableNumber(active.selection_id);
    const clubId = asNullableNumber(active.current_club_id);
    const career = selectionId !== null
      ? { managerName: asText(active.manager_name, "Manager"), careerName: asText(active.career_name, "Carreira"), targetType: "selection" as const, targetId: selectionId, targetName: asText(active.selection_name, "Seleção") }
      : clubId !== null
        ? { managerName: asText(active.manager_name, "Manager"), careerName: asText(active.career_name, "Carreira"), targetType: "club" as const, targetId: clubId, targetName: asText(active.club_name, "Clube") }
        : null;
    if (clubId === null) return { ...emptyClubWorkspace("A carreira ativa controla uma seleção; não há dados de clube para exibir."), source: { mode: "LOCAL_READ_ONLY_SQLITE", available: true, message: "A carreira ativa controla uma seleção; não há dados de clube para exibir.", generatedAt: new Date().toISOString() }, career };

    const squadSummary = db.prepare(
      `SELECT COUNT(*) AS total,
              SUM(CASE WHEN membership.status = 'Titular' THEN 1 ELSE 0 END) AS starters,
              SUM(CASE WHEN membership.status = 'Reserva' THEN 1 ELSE 0 END) AS reserves
       FROM jogador_time membership WHERE membership.time_id = ?`,
    ).get(clubId) as SQLiteRow;
    const players = db.prepare(
      `SELECT player.jogador_id, player.nome, player.idade, player.posicao, player.cr1, player.cr2, player.lado, player.estrela, player.top_mundial, membership.status, membership.categoria
       FROM jogador_time membership
       INNER JOIN jogadores player ON player.jogador_id = membership.jogador_id
       WHERE membership.time_id = ?
       ORDER BY CASE membership.status WHEN 'Titular' THEN 0 ELSE 1 END, player.posicao_codigo, player.nome
       LIMIT 32`,
    ).all(clubId) as SQLiteRow[];
    const injuryRows = tableExists(db, "injuries") ? db.prepare(
      `SELECT injury.injury_id, injury.player_id, player.nome AS player_name, injury.injury_type, injury.severity, injury.estimated_days, injury.end_date
       FROM injuries injury
       INNER JOIN jogador_time membership ON membership.jogador_id = injury.player_id
       INNER JOIN jogadores player ON player.jogador_id = injury.player_id
       WHERE membership.time_id = ? AND injury.status = 'ACTIVE'
       ORDER BY injury.end_date ASC, injury.injury_id ASC`,
    ).all(clubId) as SQLiteRow[] : [];
    const legacyFinance = tableExists(db, "club_finances") ? db.prepare("SELECT cash, updated_at FROM club_finances WHERE club_id = ?").get(clubId) as SQLiteRow | undefined : undefined;
    const ledgerColumns = tableExists(db, "financial_ledger") ? `COALESCE((SELECT SUM(amount) FROM financial_ledger WHERE club_id=state.club_id AND amount > 0), 0) AS ledger_income, COALESCE((SELECT SUM(-amount) FROM financial_ledger WHERE club_id=state.club_id AND amount < 0), 0) AS ledger_expense, COALESCE((SELECT SUM(amount) FROM financial_ledger WHERE club_id=state.club_id AND amount > 0 AND category LIKE '%SPONSOR%'), 0) AS sponsorship_income, COALESCE((SELECT SUM(amount) FROM financial_ledger WHERE club_id=state.club_id AND amount > 0 AND category LIKE '%TICKET%'), 0) AS ticket_income, COALESCE((SELECT SUM(amount) FROM financial_ledger WHERE club_id=state.club_id AND amount > 0 AND category LIKE '%PRIZE%'), 0) AS prize_income,` : `0 AS ledger_income, 0 AS ledger_expense, 0 AS sponsorship_income, 0 AS ticket_income, 0 AS prize_income,`;
    const economicFinance = tableExists(db, "club_economic_state") && tableExists(db, "club_payroll_profiles") ? db.prepare(
      `SELECT state.cash, state.budget, state.updated_at, profile.initial_cash, profile.weekly_player_payroll,
              profile.weekly_staff_payroll, profile.weekly_department_maintenance, profile.team_power,
              ${ledgerColumns}
              profile.country_factor, profile.base_level
       FROM club_economic_state state
       INNER JOIN club_payroll_profiles profile ON profile.club_id = state.club_id
       WHERE state.club_id = ?`,
    ).get(clubId) as SQLiteRow | undefined : undefined;
    const reputation = db.prepare("SELECT sporting, national, international, commercial, historical FROM club_reputation WHERE club_id = ?").get(clubId) as SQLiteRow | undefined;
    const stadiumRecord = db.prepare("SELECT name, capacity, level, status FROM club_stadiums WHERE club_id = ? AND is_primary = 1 LIMIT 1").get(clubId) as SQLiteRow | undefined;
    const stadiumName = stadiumRecord ? asText(stadiumRecord.name) : typeof active.team_stadium === "string" && active.team_stadium.trim() ? active.team_stadium : null;
    const staffMembers = tableExists(db, "staff_members") ? db.prepare(
      `SELECT staff_id, name, role, age, experience, reputation, level, specialization, status
       FROM staff_members WHERE club_id = ? AND status = 'ativo'
       ORDER BY role, name`,
    ).all(clubId) as SQLiteRow[] : [];
    const departments = tableExists(db, "club_departments") ? db.prepare(
      "SELECT department, level, capacity, efficiency FROM club_departments WHERE club_id = ? ORDER BY department",
    ).all(clubId) as SQLiteRow[] : [];
    const missions = tableExists(db, "scout_missions") ? db.prepare(
      `SELECT mission.mission_id, member.name AS scout_name, mission.status, mission.region, mission.end_date,
              (SELECT COUNT(*) FROM scout_opportunities opportunity WHERE opportunity.mission_id = mission.mission_id) AS opportunities
       FROM scout_missions mission
       LEFT JOIN staff_members member ON member.staff_id = mission.scout_id
       WHERE mission.club_id = ? ORDER BY mission.created_at DESC, mission.mission_id DESC LIMIT 20`,
    ).all(clubId) as SQLiteRow[] : [];
    const scoutingOpportunities = tableExists(db, "scout_opportunities") ? asNumber((db.prepare("SELECT COUNT(*) AS total FROM scout_opportunities WHERE club_id = ?").get(clubId) as SQLiteRow).total) : 0;
    const scoutingReports = tableExists(db, "scout_reports") && tableExists(db, "scout_missions") ? asNumber((db.prepare("SELECT COUNT(*) AS total FROM scout_reports report INNER JOIN scout_missions mission ON mission.mission_id = report.mission_id WHERE mission.club_id = ?").get(clubId) as SQLiteRow).total) : 0;
    const roleCounts = staffMembers.reduce<Record<string, number>>((counts, row) => { const role = asText(row.role, "sem_funcao"); counts[role] = (counts[role] || 0) + 1; return counts; }, {});
    const staffHistory = tableExists(db, "staff_history") ? db.prepare(
      `SELECT history.history_id, history.staff_id, history.event_type, history.event_date, history.payload
       FROM staff_history history INNER JOIN staff_members member ON member.staff_id = history.staff_id
       WHERE member.club_id = ? ORDER BY history.history_id DESC LIMIT 30`,
    ).all(clubId) as SQLiteRow[] : [];
    const effectMap: Record<string, string> = { treinador: "TACTICS", auxiliar: "TRANSITION", preparador_fisico: "PHYSICAL", medico: "HEALTH", scout: "SCOUTING" };
    const staffEffects = Object.fromEntries(Object.entries(effectMap).map(([role, effect]) => { const members = staffMembers.filter((row) => asText(row.role, "") === role); const averageLevel = members.length ? Number((members.reduce((sum, row) => sum + asNumber(row.level), 0) / members.length).toFixed(2)) : 0; return [role, { effect, members: members.length, averageLevel, bonus: Number(Math.min(0.25, averageLevel * 0.025).toFixed(4)) }]; }));
    const roleByDepartment: Record<string, string> = { medicina: "medico", preparacao_fisica: "preparador_fisico", analise: "auxiliar", base: "scout" };
    const departmentCapacity = departments.map((row) => { const department = asText(row.department); const role = roleByDepartment[department] ?? null; const used = role ? (roleCounts[role] ?? 0) : 0; const capacity = asNumber(row.capacity); return { department, capacity, used, vacancies: Math.max(0, capacity - used), role }; });
    const commissionBonus = Number(Math.min(1, Object.values(staffEffects).reduce((sum, value) => sum + value.bonus, 0)).toFixed(4));
    const parsedStaffHistory = staffHistory.map((row) => {
      let payload: Record<string, unknown> = {};
      if (typeof row.payload === "string") { try { const decoded = JSON.parse(row.payload); if (decoded && typeof decoded === "object" && !Array.isArray(decoded)) payload = decoded as Record<string, unknown>; } catch { payload = {}; } }
      return { historyId: asNumber(row.history_id), staffId: asNumber(row.staff_id), eventType: asText(row.event_type), eventDate: asText(row.event_date), payload };
    });

    return {
      source: { mode: "LOCAL_READ_ONLY_SQLITE", available: true, message: "Resumo consultado diretamente no estado SQLite do motor em modo somente leitura.", generatedAt: new Date().toISOString() },
      career,
      club: { clubId, name: asText(active.club_name, "Clube"), stadiumName },
      squad: { total: asNumber(squadSummary.total), starters: asNumber(squadSummary.starters), reserves: asNumber(squadSummary.reserves), injured: injuryRows.length, players: players.map((row) => ({ playerId: asNumber(row.jogador_id), name: asText(row.nome), age: asNumber(row.idade), position: asText(row.posicao), status: asText(row.status), category: asText(row.categoria), cr1: asNumber(row.cr1), cr2: asNumber(row.cr2), side: typeof row.lado === "string" && row.lado.trim() ? row.lado : null, star: asNumber(row.estrela) === 1, topWorld: asNumber(row.top_mundial) === 1 })) },
      finance: economicFinance
        ? {
            cash: asNullableNumber(economicFinance.cash),
            updatedAt: typeof economicFinance.updated_at === "string" ? economicFinance.updated_at : null,
            source: "ECONOMIC_PROFILE",
            budget: asNullableNumber(economicFinance.budget),
            initialCash: asNullableNumber(economicFinance.initial_cash),
            weeklyPlayerPayroll: asNullableNumber(economicFinance.weekly_player_payroll),
            weeklyStaffPayroll: asNullableNumber(economicFinance.weekly_staff_payroll),
            weeklyDepartmentMaintenance: asNullableNumber(economicFinance.weekly_department_maintenance),
            weeklyTotal: asNumber(economicFinance.weekly_player_payroll) + asNumber(economicFinance.weekly_staff_payroll) + asNumber(economicFinance.weekly_department_maintenance),
            teamPower: asNullableNumber(economicFinance.team_power),
            countryFactor: asNullableNumber(economicFinance.country_factor),
            baseLevel: asNullableNumber(economicFinance.base_level),
            ledgerIncome: asNullableNumber(economicFinance.ledger_income),
            ledgerExpense: asNullableNumber(economicFinance.ledger_expense),
            projectedCash39Weeks: asNumber(economicFinance.cash) + Math.round((asNumber(economicFinance.ledger_income) - asNumber(economicFinance.ledger_expense)) * 39 / Math.max(1, asNumber(economicFinance.weekly_player_payroll) + asNumber(economicFinance.weekly_staff_payroll) + asNumber(economicFinance.weekly_department_maintenance))),
            sponsorshipIncome: asNullableNumber(economicFinance.sponsorship_income), ticketIncome: asNullableNumber(economicFinance.ticket_income), prizeIncome: asNullableNumber(economicFinance.prize_income),
          }
        : legacyFinance
          ? { cash: asNullableNumber(legacyFinance.cash), updatedAt: typeof legacyFinance.updated_at === "string" ? legacyFinance.updated_at : null, source: "LEGACY_FINANCE", budget: null, initialCash: null, weeklyPlayerPayroll: null, weeklyStaffPayroll: null, weeklyDepartmentMaintenance: null, weeklyTotal: null, teamPower: null, countryFactor: null, baseLevel: null, ledgerIncome: null, ledgerExpense: null, projectedCash39Weeks: null, sponsorshipIncome: null, ticketIncome: null, prizeIncome: null }
          : { cash: null, updatedAt: null, source: "UNAVAILABLE", budget: null, initialCash: null, weeklyPlayerPayroll: null, weeklyStaffPayroll: null, weeklyDepartmentMaintenance: null, weeklyTotal: null, teamPower: null, countryFactor: null, baseLevel: null, ledgerIncome: null, ledgerExpense: null, projectedCash39Weeks: null, sponsorshipIncome: null, ticketIncome: null, prizeIncome: null },
      reputation: { sporting: reputation ? asNullableNumber(reputation.sporting) : null, national: reputation ? asNullableNumber(reputation.national) : null, international: reputation ? asNullableNumber(reputation.international) : null, commercial: reputation ? asNullableNumber(reputation.commercial) : null, historical: reputation ? asNullableNumber(reputation.historical) : null },
      stadium: { name: stadiumName, capacity: stadiumRecord ? asNullableNumber(stadiumRecord.capacity) : null, level: stadiumRecord ? asNullableNumber(stadiumRecord.level) : null, status: stadiumRecord && typeof stadiumRecord.status === "string" ? stadiumRecord.status : null, source: stadiumRecord ? "CLUB_STADIUM" : stadiumName ? "TEAM_RECORD" : "UNAVAILABLE" },
      training: { available: false, message: "O estado do motor ainda não possui CT persistido para este clube." },
      staff: { members: staffMembers.map((row) => ({ staffId: asNumber(row.staff_id), name: asText(row.name), role: asText(row.role), age: asNumber(row.age), experience: asNumber(row.experience), reputation: asNumber(row.reputation), level: asNumber(row.level), specialization: typeof row.specialization === "string" && row.specialization.trim() ? row.specialization : null, status: asText(row.status) })), departments: departments.map((row) => ({ department: asText(row.department), level: asNumber(row.level), capacity: asNumber(row.capacity), efficiency: asNumber(row.efficiency) })), roleCounts, averageLevel: staffMembers.length ? Number((staffMembers.reduce((sum, row) => sum + asNumber(row.level), 0) / staffMembers.length).toFixed(2)) : 0, history: parsedStaffHistory, effects: staffEffects, departmentCapacity, commissionBonus },
      health: { activeInjuries: injuryRows.map((row) => ({ injuryId: asNumber(row.injury_id), playerId: asNumber(row.player_id), playerName: asText(row.player_name), injuryType: asText(row.injury_type), severity: asText(row.severity), estimatedDays: asNullableNumber(row.estimated_days), endDate: typeof row.end_date === "string" ? row.end_date : null })), count: injuryRows.length },
      scouting: { missions: missions.map((row) => ({ missionId: asNumber(row.mission_id), scoutName: typeof row.scout_name === "string" ? row.scout_name : null, status: asText(row.status), region: typeof row.region === "string" ? row.region : null, endDate: asText(row.end_date), opportunities: asNumber(row.opportunities) })), opportunities: scoutingOpportunities, reports: scoutingReports },
    };
  } catch (error) {
    console.error("[Club workspace] Falha ao consultar o estado SQLite em modo somente leitura:", error);
    return emptyClubWorkspace("O estado local do motor não está disponível para leitura neste ambiente.");
  } finally {
    db?.close();
  }
}

export type ClubFinanceLedgerEntry = { ledgerId: number; date: string; season: number; week: number; type: string; category: string; amount: number; description: string; sourceType: string; sourceId: string };

export function getClubFinanceLedger(season?: number, category?: string, databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH): ClubFinanceLedgerEntry[] {
  let db: SQLiteDatabase | null = null;
  try {
    db = new DatabaseSync(databasePath, { readOnly: true });
    const active = db.prepare("SELECT current_club_id FROM manager_careers WHERE status = 'ACTIVE' ORDER BY updated_at DESC, career_id DESC LIMIT 1").get() as SQLiteRow | undefined;
    const clubId = active ? asNullableNumber(active.current_club_id) : null;
    if (clubId === null || !tableExists(db, "financial_ledger")) return [];
    const clauses = ["club_id = ?"]; const args: (number | string)[] = [clubId];
    if (season !== undefined) { clauses.push("season = ?"); args.push(season); }
    if (category) { clauses.push("category = ?"); args.push(category); }
    const rows = db.prepare(`SELECT ledger_id, date, season, week, type, category, amount, description, source_type, source_id FROM financial_ledger WHERE ${clauses.join(" AND ")} ORDER BY date DESC, ledger_id DESC LIMIT 500`).all(...args) as SQLiteRow[];
    return rows.map((row) => ({ ledgerId: asNumber(row.ledger_id), date: asText(row.date), season: asNumber(row.season), week: asNumber(row.week), type: asText(row.type), category: asText(row.category), amount: asNumber(row.amount), description: asText(row.description), sourceType: asText(row.source_type), sourceId: asText(row.source_id) }));
  } catch (error) { console.error("[Finance ledger] Falha na leitura somente leitura:", error); return []; } finally { db?.close(); }
}
