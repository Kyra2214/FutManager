import { afterEach, describe, expect, it } from "vitest";
import { createRequire } from "node:module";
import { mkdtempSync, rmSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { getClubWorkspaceDashboard } from "./engineState";

type Db = { close: () => void; exec: (sql: string) => void };
type DbConstructor = new (path: string) => Db;
const runtimeRequire = createRequire(import.meta.url);
const { DatabaseSync } = runtimeRequire(["node", "sqlite"].join(":")) as { DatabaseSync: DbConstructor };
const folders: string[] = [];

afterEach(() => {
  while (folders.length) {
    const folder = folders.pop();
    if (folder) rmSync(folder, { recursive: true, force: true });
  }
});

function fixture() {
  const folder = mkdtempSync(join(tmpdir(), "futmanager-club-"));
  folders.push(folder);
  const path = join(folder, "game.db");
  const db = new DatabaseSync(path);
  db.exec(`
    CREATE TABLE managers(manager_id INTEGER PRIMARY KEY, name TEXT NOT NULL);
    CREATE TABLE manager_careers(career_id INTEGER PRIMARY KEY, manager_id INTEGER NOT NULL, name TEXT NOT NULL, current_club_id INTEGER, status TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE TABLE manager_selection_assignments(career_id INTEGER, selection_id INTEGER, status TEXT);
    CREATE TABLE selecoes(selecao_id INTEGER PRIMARY KEY, nome TEXT);
    CREATE TABLE times(time_id INTEGER PRIMARY KEY, nome TEXT NOT NULL, estadio TEXT);
    CREATE TABLE jogadores(jogador_id INTEGER PRIMARY KEY, nome TEXT NOT NULL, idade INTEGER NOT NULL, posicao TEXT NOT NULL, posicao_codigo INTEGER NOT NULL, cr1 INTEGER NOT NULL, cr2 INTEGER NOT NULL, lado TEXT, estrela INTEGER NOT NULL DEFAULT 0, top_mundial INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE jogador_time(jogador_id INTEGER, time_id INTEGER, status TEXT, categoria TEXT);
    CREATE TABLE injuries(injury_id INTEGER PRIMARY KEY, player_id INTEGER, injury_type TEXT, start_date TEXT, estimated_days INTEGER, end_date TEXT, severity TEXT, status TEXT);
    CREATE TABLE staff_members(staff_id INTEGER PRIMARY KEY, name TEXT, role TEXT, age INTEGER, club_id INTEGER, experience INTEGER, reputation INTEGER, level INTEGER, specialization TEXT, status TEXT);
    CREATE TABLE staff_history(history_id INTEGER PRIMARY KEY, staff_id INTEGER, event_type TEXT, event_date TEXT, payload TEXT);
    CREATE TABLE club_departments(club_id INTEGER, department TEXT, level INTEGER, cost INTEGER, capacity INTEGER, maintenance INTEGER, efficiency REAL);
    CREATE TABLE scout_missions(mission_id INTEGER PRIMARY KEY, club_id INTEGER, scout_id INTEGER, start_date TEXT, end_date TEXT, region TEXT, status TEXT, created_at TEXT);
    CREATE TABLE scout_opportunities(opportunity_id INTEGER PRIMARY KEY, mission_id INTEGER, club_id INTEGER);
    CREATE TABLE scout_reports(report_id INTEGER PRIMARY KEY, mission_id INTEGER);
    CREATE TABLE club_finances(club_id INTEGER PRIMARY KEY, cash INTEGER, updated_at TEXT);
    CREATE TABLE club_economic_state(club_id INTEGER PRIMARY KEY, cash INTEGER, budget INTEGER, updated_at TEXT);
    CREATE TABLE club_payroll_profiles(club_id INTEGER PRIMARY KEY, initial_cash INTEGER, weekly_player_payroll INTEGER, weekly_staff_payroll INTEGER, weekly_department_maintenance INTEGER, team_power REAL, country_factor REAL, base_level INTEGER);
    CREATE TABLE club_reputation(club_id INTEGER PRIMARY KEY, sporting INTEGER, national INTEGER, international INTEGER, commercial INTEGER, historical INTEGER);
    CREATE TABLE club_stadiums(stadium_id INTEGER PRIMARY KEY, club_id INTEGER, name TEXT, capacity INTEGER, level INTEGER, status TEXT, is_primary INTEGER);
    INSERT INTO managers VALUES(1,'Manager Teste');
    INSERT INTO manager_careers VALUES(1,1,'Carreira Teste',9,'ACTIVE','2026-08-26T00:00:00Z');
    INSERT INTO times VALUES(9,'Clube Persistido','Estádio de Origem');
    INSERT INTO jogadores VALUES(101,'Goleiro Real',28,'Goleiro',0,72,75,'D',0,0),(102,'Meia Real',24,'Meia',3,77,81,'E',1,0),(103,'Atacante Real',22,'Atacante',4,70,84,NULL,0,1);
    INSERT INTO jogador_time VALUES(101,9,'Titular','Principal'),(102,9,'Titular','Principal'),(103,9,'Reserva','Principal');
    INSERT INTO injuries VALUES(1,102,'Lesão muscular','2026-08-20',14,'2026-09-03','MODERATE','ACTIVE');
    INSERT INTO staff_members VALUES(1,'Auxiliar Real','auxiliar',42,9,70,65,5,'transição','ativo'),(2,'Médica Real','medico',37,9,80,72,6,'fisiologia','ativo'),(3,'Scout Real','scout',45,9,62,58,4,'América do Sul','ativo');
    INSERT INTO staff_history VALUES(1,1,'STAFF_CREATED','2026-08-01','{"role":"auxiliar"}');
    INSERT INTO club_departments VALUES(9,'medicina',4,100,5,10,0.6);
    INSERT INTO scout_missions VALUES(1,9,3,'2026-08-01','2026-09-01','América do Sul','ACTIVE','2026-08-01');
    INSERT INTO scout_opportunities VALUES(1,1,9);
    INSERT INTO scout_reports VALUES(1,1);
    INSERT INTO club_finances VALUES(9,750000,'2026-08-26T00:00:00Z');
    INSERT INTO club_economic_state VALUES(9,975000,975000,'2026-08-27T00:00:00Z');
    INSERT INTO club_payroll_profiles VALUES(9,975000,21000,4500,1200,84.5,1.1,2);
    INSERT INTO club_reputation VALUES(9,72,65,40,60,88);
    INSERT INTO club_stadiums VALUES(1,9,'Estádio Persistido',42000,3,'OPEN',1);
  `);
  db.close();
  return path;
}

describe("getClubWorkspaceDashboard", () => {
  it("deriva carreira, elenco e estruturas a partir do SQLite somente leitura", () => {
    const dashboard = getClubWorkspaceDashboard(fixture());
    expect(dashboard.source.available).toBe(true);
    expect(dashboard.career).toMatchObject({ managerName: "Manager Teste", targetType: "club", targetId: 9 });
    expect(dashboard.club).toMatchObject({ name: "Clube Persistido", stadiumName: "Estádio Persistido" });
    expect(dashboard.squad).toMatchObject({ total: 3, starters: 2, reserves: 1, injured: 1 });
    expect(dashboard.squad.players[0]).toMatchObject({ name: "Goleiro Real", status: "Titular" });
    expect(dashboard.finance).toMatchObject({ cash: 975000, source: "ECONOMIC_PROFILE", budget: 975000, initialCash: 975000, weeklyPlayerPayroll: 21000, weeklyStaffPayroll: 4500, weeklyDepartmentMaintenance: 1200, weeklyTotal: 26700, teamPower: 84.5, countryFactor: 1.1, baseLevel: 2 });
    expect(dashboard.reputation.sporting).toBe(72);
    expect(dashboard.stadium).toMatchObject({ source: "CLUB_STADIUM", capacity: 42000, level: 3 });
    expect(dashboard.training.available).toBe(false);
    expect(dashboard.staff.members).toHaveLength(3);
    expect(dashboard.staff.roleCounts).toMatchObject({ auxiliar: 1, medico: 1, scout: 1 });
    expect(dashboard.staff.averageLevel).toBe(5);
    expect(dashboard.staff.history[0]).toMatchObject({ staffId: 1, eventType: "STAFF_CREATED", payload: { role: "auxiliar" } });
    expect(dashboard.staff.effects.medico).toMatchObject({ effect: "HEALTH", members: 1, averageLevel: 6, bonus: 0.15 });
    expect(dashboard.staff.commissionBonus).toBeCloseTo(0.375, 3);
    expect(dashboard.staff.departmentCapacity[0]).toMatchObject({ department: "medicina", capacity: 5, used: 1, vacancies: 4, role: "medico" });
    expect(dashboard.staff.departments[0]).toMatchObject({ department: "medicina", level: 4 });
    expect(dashboard.health.activeInjuries[0]).toMatchObject({ playerName: "Meia Real", injuryType: "Lesão muscular" });
    expect(dashboard.scouting).toMatchObject({ opportunities: 1, reports: 1 });
    expect(dashboard.scouting.missions[0]).toMatchObject({ scoutName: "Scout Real", opportunities: 1 });
  });
});
