import { afterEach, describe, expect, it } from "vitest";
import { mkdtempSync, rmSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { getMatchesDashboard, getPlayerContracts, getPlayerSeasonTotals, previewContractRenewal } from "./engineState";

type WritableSQLiteDatabase = {
  close: () => void;
  exec: (statement: string) => void;
};

type WritableSQLiteDatabaseConstructor = new (path: string) => WritableSQLiteDatabase;

const runtimeRequire = createRequire(import.meta.url);
const { DatabaseSync } = runtimeRequire(["node", "sqlite"].join(":")) as {
  DatabaseSync: WritableSQLiteDatabaseConstructor;
};

const temporaryFolders: string[] = [];

afterEach(() => {
  while (temporaryFolders.length) {
    const folder = temporaryFolders.pop();
    if (folder) rmSync(folder, { recursive: true, force: true });
  }
});

function createEngineFixture() {
  const directory = mkdtempSync(join(tmpdir(), "futmanager-engine-"));
  temporaryFolders.push(directory);
  const databasePath = join(directory, "game.db");
  const db = new DatabaseSync(databasePath);

  db.exec(`
    CREATE TABLE times (time_id INTEGER PRIMARY KEY, nome TEXT NOT NULL);
    CREATE TABLE jogadores (jogador_id INTEGER PRIMARY KEY, nome TEXT NOT NULL);
    CREATE TABLE seasons (season_id INTEGER PRIMARY KEY, year INTEGER NOT NULL);
    CREATE TABLE competitions (competition_id INTEGER PRIMARY KEY, name TEXT NOT NULL, season_id INTEGER NOT NULL, type TEXT NOT NULL, format TEXT NOT NULL, status TEXT NOT NULL);
    CREATE TABLE competition_entries (competition_id INTEGER NOT NULL, club_id INTEGER NOT NULL);
    CREATE TABLE competition_config (competition_id INTEGER PRIMARY KEY, tiebreakers TEXT NOT NULL DEFAULT 'points,wins,goal_difference,goals_for');
    CREATE TABLE team_competition_stats (competition_id INTEGER NOT NULL, club_id INTEGER NOT NULL, played INTEGER, wins INTEGER, draws INTEGER, losses INTEGER, goals_for INTEGER, goals_against INTEGER, points INTEGER);
    CREATE TABLE competition_phases (phase_id INTEGER PRIMARY KEY, competition_id INTEGER NOT NULL, name TEXT, order_no INTEGER NOT NULL DEFAULT 1, status TEXT NOT NULL DEFAULT 'PLANNED');
    CREATE TABLE competition_rounds (round_id INTEGER PRIMARY KEY, number INTEGER NOT NULL, phase_id INTEGER);
    CREATE TABLE fixtures (fixture_id INTEGER PRIMARY KEY, competition_id INTEGER NOT NULL, round_id INTEGER NOT NULL, home_club_id INTEGER NOT NULL, away_club_id INTEGER NOT NULL, scheduled_at TEXT NOT NULL, status TEXT NOT NULL, match_id INTEGER);
    CREATE TABLE matches (match_id INTEGER PRIMARY KEY, competition_id INTEGER NOT NULL, match_date TEXT NOT NULL, round INTEGER NOT NULL, home_club_id INTEGER NOT NULL, away_club_id INTEGER NOT NULL, home_goals INTEGER, away_goals INTEGER, status TEXT NOT NULL);
    CREATE TABLE manager_careers (career_id INTEGER PRIMARY KEY, current_club_id INTEGER, status TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE player_match_stats (match_id INTEGER NOT NULL, player_id INTEGER NOT NULL, minutes INTEGER, goals INTEGER, assists INTEGER, cards INTEGER, rating REAL, PRIMARY KEY(match_id, player_id));
    CREATE TABLE player_contract_history (contract_id INTEGER PRIMARY KEY, player_id INTEGER, club_id INTEGER, start_season INTEGER, start_week INTEGER, end_season INTEGER, end_week INTEGER, weekly_salary INTEGER, release_clause INTEGER, status TEXT, source TEXT);
    CREATE TABLE club_payroll_profiles (club_id INTEGER PRIMARY KEY, weekly_player_payroll INTEGER);
  `);
  db.exec(`
    INSERT INTO times VALUES (1, 'Clube da Capital'), (2, 'Atlético do Vale');
    INSERT INTO jogadores VALUES (7, 'Atleta Teste'), (8, 'Segundo Atleta');
    INSERT INTO seasons VALUES (7, 2026);
    INSERT INTO competitions VALUES (11, 'Liga Nacional', 7, 'LEAGUE', 'ROUND_ROBIN', 'ACTIVE');
    INSERT INTO competition_entries VALUES (11, 1), (11, 2);
    INSERT INTO competition_config VALUES (11, 'points,wins,goal_difference,goals_for');
    INSERT INTO team_competition_stats VALUES (11, 1, 1, 1, 0, 0, 2, 0, 3), (11, 2, 1, 0, 0, 1, 0, 2, 0);
    INSERT INTO competition_phases VALUES (21, 11, 'Regular', 1, 'ACTIVE');
    INSERT INTO competition_rounds VALUES (31, 2, 21);
    INSERT INTO fixtures VALUES (101, 11, 31, 1, 2, '2026-08-30T18:00:00Z', 'SCHEDULED', NULL);
    INSERT INTO matches VALUES (201, 11, '2026-08-23T18:00:00Z', 1, 1, 2, 2, 0, 'PLAYED');
    INSERT INTO manager_careers VALUES (5, 1, 'ACTIVE', '2026-08-20T12:00:00Z');
    INSERT INTO player_match_stats VALUES (201, 7, 90, 2, 1, 0, 8.0), (201, 8, 90, 0, 2, 1, 8.5);
    INSERT INTO player_contract_history VALUES (1, 7, 1, 2026, 1, 2026, 5, 1000, 50000, 'ACTIVE', 'test');
    INSERT INTO club_payroll_profiles VALUES (1, 2000);
  `);
  db.close();
  return databasePath;
}

describe("getMatchesDashboard", () => {
  it("deriva competição, tabela, calendário e resultados a partir de um SQLite somente leitura", () => {
    const dashboard = getMatchesDashboard(undefined, createEngineFixture());

    expect(dashboard.source.available).toBe(true);
    expect(dashboard.controlledClub).toEqual({ clubId: 1, name: "Clube da Capital" });
    expect(dashboard.selectedCompetition?.name).toBe("Liga Nacional");
    expect(dashboard.standings[0]).toMatchObject({ position: 1, clubName: "Clube da Capital", points: 3 });
    expect(dashboard.upcomingFixtures[0]).toMatchObject({ status: "SCHEDULED", round: 2 });
    expect(dashboard.recentResults[0]).toMatchObject({ homeGoals: 2, awayGoals: 0, isPlayed: true });
  });

  it("lê contratos próximos do vencimento e calcula prévia sem persistir", () => {
    const databasePath = createEngineFixture();
    const contracts = getPlayerContracts(1, 2026, 1, 8, databasePath);
    expect(contracts.contracts[0]).toMatchObject({ playerId: 7, weeksRemaining: 4, weeklySalary: 1000 });
    const preview = previewContractRenewal(7, 1, 1300, databasePath);
    expect(preview).toMatchObject({ weeklyDelta: 300, currentClubPayroll: 2000, projectedClubPayroll: 2300, persisted: false });
    const runtimeRequire = createRequire(import.meta.url);
    const check = runtimeRequire(["node", "sqlite"].join(":")) as { DatabaseSync: WritableSQLiteDatabaseConstructor };
    const db = new check.DatabaseSync(databasePath);
    expect((db.prepare("SELECT weekly_salary FROM player_contract_history WHERE contract_id=1").get() as { weekly_salary: number }).weekly_salary).toBe(1000);
    db.close();
  });

  it("lê agregados de atletas filtrados pela competição sem escrever no banco", () => {
    const stats = getPlayerSeasonTotals(11, undefined, createEngineFixture());
    expect(stats.source.available).toBe(true);
    expect(stats.players[0]).toMatchObject({ playerId: 7, goals: 2, assists: 1, appearances: 1 });
    expect(stats.players[1]).toMatchObject({ playerId: 8, cards: 1 });
  });
});
