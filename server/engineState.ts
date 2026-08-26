import { createRequire } from "node:module";

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

const DEFAULT_ENGINE_STATE_PATH = "/home/ubuntu/brasfoot_engine/data/state/game.db";
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

export type MatchesDashboard = {
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
  };
  reputation: { sporting: number | null; national: number | null; international: number | null; commercial: number | null; historical: number | null };
  stadium: { name: string | null; capacity: number | null; level: number | null; status: string | null; source: "CLUB_STADIUM" | "TEAM_RECORD" | "UNAVAILABLE" };
  training: { available: boolean; message: string };
  staff: { members: Array<{ staffId: number; name: string; role: string; age: number; experience: number; reputation: number; level: number; specialization: string | null; status: string }>; departments: Array<{ department: string; level: number; capacity: number; efficiency: number }>; roleCounts: Record<string, number> };
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

function getCompetitionRows(db: SQLiteDatabase): CompetitionSummary[] {
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
         (SELECT COUNT(*) FROM matches game WHERE game.competition_id = competition.competition_id AND game.status = 'PLAYED') AS played_matches
       FROM competitions competition
       LEFT JOIN seasons season ON season.season_id = competition.season_id
       ORDER BY
         CASE competition.status WHEN 'ACTIVE' THEN 0 WHEN 'PLANNED' THEN 1 ELSE 2 END,
         season.year DESC,
         competition.competition_id DESC`,
    )
    .all() as SQLiteRow[];

  return rows.map(toCompetition);
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

function getMatches(db: SQLiteDatabase, competitionId: number): MatchCard[] {
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
         AND NOT EXISTS (SELECT 1 FROM fixtures fixture WHERE fixture.match_id = game.match_id)
       ORDER BY scheduled_at ASC, round_number ASC`,
    )
    .all(competitionId, competitionId) as SQLiteRow[];

  return rows.map(toMatchCard);
}

export function getMatchesDashboard(
  competitionId?: number,
  databasePath = process.env.FUTMANAGER_ENGINE_STATE_PATH || DEFAULT_ENGINE_STATE_PATH,
): MatchesDashboard {
  let db: SQLiteDatabase | null = null;

  try {
    db = new DatabaseSync(databasePath, { readOnly: true });
    const controlledClub = getControlledClub(db);
    const competitions = getCompetitionRows(db);
    const selectedCompetition =
      competitions.find((competition) => competition.competitionId === competitionId) ?? competitions[0] ?? null;

    if (!selectedCompetition) {
      return {
        ...emptyDashboard("O motor está conectado, mas ainda não há competições persistidas na carreira."),
        source: {
          mode: "LOCAL_READ_ONLY_SQLITE",
          available: true,
          message: "O motor está conectado, mas ainda não há competições persistidas na carreira.",
          generatedAt: new Date().toISOString(),
        },
        controlledClub,
      };
    }

    const allMatches = getMatches(db, selectedCompetition.competitionId);
    return {
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
      standings: getStandings(db, selectedCompetition.competitionId, controlledClub?.clubId ?? null),
      upcomingFixtures: allMatches.filter((match) => !match.isPlayed),
      recentResults: allMatches.filter((match) => match.isPlayed).reverse(),
    };
  } catch (error) {
    console.error("[Engine state] Falha ao consultar o estado SQLite em modo somente leitura:", error);
    return emptyDashboard("O estado local do motor não está disponível para leitura neste ambiente.");
  } finally {
    db?.close();
  }
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
    finance: { cash: null, updatedAt: null, source: "UNAVAILABLE", budget: null, initialCash: null, weeklyPlayerPayroll: null, weeklyStaffPayroll: null, weeklyDepartmentMaintenance: null, weeklyTotal: null, teamPower: null, countryFactor: null, baseLevel: null },
    reputation: { sporting: null, national: null, international: null, commercial: null, historical: null },
    stadium: { name: null, capacity: null, level: null, status: null, source: "UNAVAILABLE" },
    training: { available: false, message: "O estado do motor ainda não possui CT persistido para este clube." },
    staff: { members: [], departments: [], roleCounts: {} },
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
    const economicFinance = tableExists(db, "club_economic_state") && tableExists(db, "club_payroll_profiles") ? db.prepare(
      `SELECT state.cash, state.budget, state.updated_at, profile.initial_cash, profile.weekly_player_payroll,
              profile.weekly_staff_payroll, profile.weekly_department_maintenance, profile.team_power,
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
          }
        : legacyFinance
          ? { cash: asNullableNumber(legacyFinance.cash), updatedAt: typeof legacyFinance.updated_at === "string" ? legacyFinance.updated_at : null, source: "LEGACY_FINANCE", budget: null, initialCash: null, weeklyPlayerPayroll: null, weeklyStaffPayroll: null, weeklyDepartmentMaintenance: null, weeklyTotal: null, teamPower: null, countryFactor: null, baseLevel: null }
          : { cash: null, updatedAt: null, source: "UNAVAILABLE", budget: null, initialCash: null, weeklyPlayerPayroll: null, weeklyStaffPayroll: null, weeklyDepartmentMaintenance: null, weeklyTotal: null, teamPower: null, countryFactor: null, baseLevel: null },
      reputation: { sporting: reputation ? asNullableNumber(reputation.sporting) : null, national: reputation ? asNullableNumber(reputation.national) : null, international: reputation ? asNullableNumber(reputation.international) : null, commercial: reputation ? asNullableNumber(reputation.commercial) : null, historical: reputation ? asNullableNumber(reputation.historical) : null },
      stadium: { name: stadiumName, capacity: stadiumRecord ? asNullableNumber(stadiumRecord.capacity) : null, level: stadiumRecord ? asNullableNumber(stadiumRecord.level) : null, status: stadiumRecord && typeof stadiumRecord.status === "string" ? stadiumRecord.status : null, source: stadiumRecord ? "CLUB_STADIUM" : stadiumName ? "TEAM_RECORD" : "UNAVAILABLE" },
      training: { available: false, message: "O estado do motor ainda não possui CT persistido para este clube." },
      staff: { members: staffMembers.map((row) => ({ staffId: asNumber(row.staff_id), name: asText(row.name), role: asText(row.role), age: asNumber(row.age), experience: asNumber(row.experience), reputation: asNumber(row.reputation), level: asNumber(row.level), specialization: typeof row.specialization === "string" && row.specialization.trim() ? row.specialization : null, status: asText(row.status) })), departments: departments.map((row) => ({ department: asText(row.department), level: asNumber(row.level), capacity: asNumber(row.capacity), efficiency: asNumber(row.efficiency) })), roleCounts },
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
