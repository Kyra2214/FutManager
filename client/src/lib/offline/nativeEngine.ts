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

export type NativeEnginePlugin = {
  startCareer(input: NativeCareerStartInput): Promise<NativeCareerResult>;
  advanceWeek(input?: { seed?: string }): Promise<{ season: number; week: number; events: unknown[] }>;
  playControlledMatch(input: { matchId: number; decision?: Record<string, unknown> }): Promise<Record<string, unknown>>;
};

export const NativeEngine = registerPlugin<NativeEnginePlugin>("NativeEngine");
