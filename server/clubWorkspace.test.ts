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
    CREATE TABLE jogadores(jogador_id INTEGER PRIMARY KEY, nome TEXT NOT NULL, posicao TEXT NOT NULL, posicao_codigo INTEGER NOT NULL);
    CREATE TABLE jogador_time(jogador_id INTEGER, time_id INTEGER, status TEXT, categoria TEXT);
    CREATE TABLE injuries(injury_id INTEGER PRIMARY KEY, player_id INTEGER, status TEXT);
    CREATE TABLE club_finances(club_id INTEGER PRIMARY KEY, cash INTEGER, updated_at TEXT);
    CREATE TABLE club_reputation(club_id INTEGER PRIMARY KEY, sporting INTEGER, national INTEGER, international INTEGER, commercial INTEGER, historical INTEGER);
    CREATE TABLE club_stadiums(stadium_id INTEGER PRIMARY KEY, club_id INTEGER, name TEXT, capacity INTEGER, level INTEGER, status TEXT, is_primary INTEGER);
    INSERT INTO managers VALUES(1,'Manager Teste');
    INSERT INTO manager_careers VALUES(1,1,'Carreira Teste',9,'ACTIVE','2026-08-26T00:00:00Z');
    INSERT INTO times VALUES(9,'Clube Persistido','Estádio de Origem');
    INSERT INTO jogadores VALUES(101,'Goleiro Real','Goleiro',0),(102,'Meia Real','Meia',3),(103,'Atacante Real','Atacante',4);
    INSERT INTO jogador_time VALUES(101,9,'Titular','Principal'),(102,9,'Titular','Principal'),(103,9,'Reserva','Principal');
    INSERT INTO injuries VALUES(1,102,'ACTIVE');
    INSERT INTO club_finances VALUES(9,750000,'2026-08-26T00:00:00Z');
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
    expect(dashboard.finance.cash).toBe(750000);
    expect(dashboard.reputation.sporting).toBe(72);
    expect(dashboard.stadium).toMatchObject({ source: "CLUB_STADIUM", capacity: 42000, level: 3 });
    expect(dashboard.training.available).toBe(false);
  });
});
