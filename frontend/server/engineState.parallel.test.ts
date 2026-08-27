import { describe, expect, it } from 'vitest';
import { createRequire } from 'node:module';
import { mkdtempSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { getMatchesDashboard } from './engineState';
const runtimeRequire = createRequire(import.meta.url);
const { DatabaseSync } = runtimeRequire('node:sqlite') as { new (path: string): { exec(sql: string): void; close(): void } };

describe('parallel engine state fallback', () => {
  it('lê fixtures materializados pelo motor Python quando o catálogo canônico está vazio', () => {
    const dir = mkdtempSync(join(tmpdir(), 'futmanager-parallel-')); const path = join(dir, 'state.db'); const db = new DatabaseSync(path);
    db.exec(`CREATE TABLE manager_careers(career_id INTEGER PRIMARY KEY, status TEXT, current_club_id INTEGER, updated_at TEXT); CREATE TABLE times(time_id INTEGER PRIMARY KEY, nome TEXT); CREATE TABLE career_parallel_leagues(career_id INTEGER PRIMARY KEY, manager_id INTEGER, name TEXT, season_id INTEGER, total_clubs INTEGER, source_country_count INTEGER, seed TEXT, division_count INTEGER, created_at TEXT); CREATE TABLE career_parallel_standings(career_id INTEGER, season_number INTEGER, club_id INTEGER, division INTEGER, position INTEGER, played INTEGER, wins INTEGER, draws INTEGER, losses INTEGER, goals_for INTEGER, goals_against INTEGER, points INTEGER, updated_at TEXT); CREATE TABLE career_parallel_fixtures(fixture_id INTEGER PRIMARY KEY, career_id INTEGER, season_number INTEGER, matchday INTEGER, leg INTEGER, division INTEGER, scheduled_date TEXT, home_club_id INTEGER, away_club_id INTEGER, status TEXT, home_goals INTEGER, away_goals INTEGER); INSERT INTO manager_careers VALUES(3,'ACTIVE',3280,'2026-08-27'); INSERT INTO times VALUES(3280,'Flamengo'),(12,'Clube A'); INSERT INTO career_parallel_leagues VALUES(3,3,'Minha carreira · Liga Mundial',1,80,4,'seed',4,'2026-08-27'); INSERT INTO career_parallel_standings VALUES(3,1,3280,4,1,0,0,0,0,0,0,0,'2026-08-27'); INSERT INTO career_parallel_fixtures VALUES(1,3,1,1,1,4,'2026-08-01',3280,12,'SCHEDULED',NULL,NULL);`); db.close();
    const dashboard = getMatchesDashboard(undefined, path); expect(dashboard.selectedCompetition?.name).toContain('Minha carreira'); expect(dashboard.selectedCompetition?.registeredClubs).toBe(80); expect(dashboard.upcomingFixtures).toHaveLength(1); expect(dashboard.upcomingFixtures[0]).toMatchObject({ homeClub: { clubId: 3280, name: 'Flamengo' }, status: 'SCHEDULED' }); expect(dashboard.standings[0].clubId).toBe(3280); rmSync(dir, { recursive: true, force: true });
  });
});
