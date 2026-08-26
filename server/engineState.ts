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
