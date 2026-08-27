import { registerPlugin } from "@capacitor/core";

export type NativeCareerStartInput = {
  managerName: string;
  nationality?: string;
  age: number;
  careerName: string;
  targetType: "club" | "selection";
  targetId: number;
  selectedCountryIds: number[];
};

export type NativeCareerResult = {
  managerId: number;
  careerId: number;
  targetType: "club" | "selection";
  targetId: number;
  currentClubId: number | null;
  worldMode: "NATIONAL" | "PARALLEL";
  startingDivision: number;
};

export type NativeMatchCard = {
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

export type NativeDashboard = {
  filters: { competitionId: number | null; season: number | null; phaseId: number | null };
  source: { mode: "LOCAL_READ_ONLY_SQLITE"; available: boolean; message: string; generatedAt: string };
  controlledClub: { clubId: number; name: string } | null;
  competitions: Array<{ competitionId: number; name: string; type: string; format: string; status: string; seasonId: number; seasonYear: number | null; registeredClubs: number; scheduledFixtures: number; playedMatches: number; currentPhase: { phaseId: number; name: string; status: string } | null; tiebreakers: string[] }>;
  selectedCompetitionId: number | null;
  selectedCompetition: NativeDashboard["competitions"][number] | null;
  standings: Array<{ position: number; clubId: number; clubName: string; played: number; wins: number; draws: number; losses: number; goalsFor: number; goalsAgainst: number; goalDifference: number; points: number; isControlledClub: boolean }>;
  upcomingFixtures: NativeMatchCard[];
  recentResults: NativeMatchCard[];
};

export type NativeEnginePlugin = {
  getDashboard(input?: { competitionId?: number }): Promise<NativeDashboard>;
  advanceUntilMatch(input: { matchId: number; seed?: number }): Promise<{ status: string; match_id: number; weeks_advanced: number; target_season: number | null; target_round: number | null; notice: string | null; cycles: Array<{ season: number; week: number; matches: number; world_events: unknown[] }> }>;
  startCareer(input: NativeCareerStartInput): Promise<NativeCareerResult>;
  advanceWeek(input?: { seed?: string }): Promise<{ season: number; week: number; events: unknown[] }>;
  playControlledMatch(input: { matchId: number; decision?: Record<string, unknown> }): Promise<Record<string, unknown>>;
};

export const NativeEngine = registerPlugin<NativeEnginePlugin>("NativeEngine");
