export type OfflineEntityId = string | number;

export interface OfflineCareerSummary {
  careerId: OfflineEntityId;
  managerName: string;
  careerName: string;
  controlledEntityId: OfflineEntityId;
  season: number;
  week: number;
}

export interface OfflineFixtureTarget {
  matchId: OfflineEntityId;
  season: number;
  week: number;
  homeClubId: OfflineEntityId;
  awayClubId: OfflineEntityId;
}

export interface OfflineTravelEvent {
  id: OfflineEntityId;
  season: number;
  week: number;
  kind: string;
  title: string;
  description: string;
  read: boolean;
}

export interface OfflineTravelSummary {
  target: OfflineFixtureTarget;
  weeksAdvanced: number;
  events: OfflineTravelEvent[];
}

export interface OfflineMatchDecision {
  mentality?: "defensive" | "balanced" | "offensive";
  formation?: string;
  attackLane?: "wings" | "middle";
  passing?: "short" | "long" | "sideways";
  pressure?: "low" | "medium" | "high";
  crossing?: "rare" | "normal" | "frequent";
}

export interface OfflineMatchResult {
  matchId: OfflineEntityId;
  season: number;
  week: number;
  status: "scheduled" | "live" | "finished";
  homeScore: number | null;
  awayScore: number | null;
  events: Array<{
    id: OfflineEntityId;
    minute: number;
    kind: string;
    description: string;
  }>;
}

export interface OfflineAssetReference {
  entityId: OfflineEntityId;
  kind: "club" | "selection";
  path: string | null;
}

export interface OfflineCareerDomain {
  getCurrentCareer(): Promise<OfflineCareerSummary | null>;
  advanceWeek(): Promise<{ season: number; week: number; events: OfflineTravelEvent[] }>;
  advanceUntilMatch(target: OfflineFixtureTarget): Promise<OfflineTravelSummary>;
  playControlledMatch(
    matchId: OfflineEntityId,
    decision?: OfflineMatchDecision,
  ): Promise<OfflineMatchResult>;
  listEvents(): Promise<OfflineTravelEvent[]>;
  markEventRead(eventId: OfflineEntityId): Promise<void>;
  resolveAsset(entityId: OfflineEntityId): Promise<OfflineAssetReference>;
}
