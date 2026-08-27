import {
  isOfflineNativeRuntime,
  queryLocal,
  readLocalGameState,
  writeLocalGameState,
} from "./localStore";
import { listLocalClubs, listLocalSelections, resolveLocalAsset } from "./localCatalog";
import { NativeEngine, type NativeCareerStartInput, type NativeDashboard } from "./nativeEngine";

export type LocalCareerState = Record<string, unknown>;

type CareerRow = {
  career_id: number;
  name: string;
  current_club_id: number | null;
  season_id: number | null;
  status: string;
};

export async function loadActiveCareerFromGameState() {
  const rows = await queryLocal<CareerRow>(`
    SELECT career_id, name, current_club_id, season_id, status
    FROM manager_careers
    WHERE status NOT IN ('ARCHIVED', 'DELETED')
    ORDER BY updated_at DESC, career_id DESC
    LIMIT 1
  `);
  const career = rows[0];
  if (!career) return null;
  return {
    careerId: career.career_id,
    careerName: career.name,
    controlledClubId: career.current_club_id,
    seasonId: career.season_id,
    status: career.status,
  };
}

export type LocalRuntimeStatus =
  | { ready: true; platform: "android" }
  | { ready: false; reason: "browser-preview" };

export function getLocalRuntimeStatus(): LocalRuntimeStatus {
  return isOfflineNativeRuntime()
    ? { ready: true, platform: "android" }
    : { ready: false, reason: "browser-preview" };
}

/**
 * Transitional domain boundary for the offline application.
 * Business rules belong here, while persistence remains exclusively in localStore.
 */
export const localDomain = {
  status: getLocalRuntimeStatus,

  async loadCareer() {
    return readLocalGameState<LocalCareerState>();
  },

  async loadActiveCareer() {
    return loadActiveCareerFromGameState();
  },

  async loadMatchesDashboard(competitionId?: number): Promise<NativeDashboard> {
    if (!isOfflineNativeRuntime()) return Promise.reject(new Error("O dashboard local só está disponível no aplicativo instalado."));
    return NativeEngine.getDashboard(competitionId ? { competitionId } : undefined);
  },

  async advanceUntilMatch(matchId: number, seed?: number) {
    if (!isOfflineNativeRuntime()) return Promise.reject(new Error("A viagem local só está disponível no aplicativo instalado."));
    return NativeEngine.advanceUntilMatch({ matchId, ...(seed === undefined ? {} : { seed }) });
  },

  async listClubs(search = "", limit = 48) {
    return listLocalClubs(search, limit);
  },

  async listSelections(search = "", limit = 48) {
    return listLocalSelections(search, limit);
  },

  async resolveAsset(entityType: "team" | "selection", entityId: number) {
    return resolveLocalAsset(entityType, entityId);
  },

  async startCareer(input: NativeCareerStartInput) {
    if (!isOfflineNativeRuntime()) return Promise.reject(new Error("A criação local só está disponível no aplicativo instalado."));
    return NativeEngine.startCareer(input);
  },

  async advanceWeek(seed?: string) {
    if (!isOfflineNativeRuntime()) return Promise.reject(new Error("O avanço local só está disponível no aplicativo instalado."));
    return NativeEngine.advanceWeek(seed ? { seed } : undefined);
  },

  async playControlledMatch(matchId: number, decision?: Record<string, unknown>) {
    if (!isOfflineNativeRuntime()) return Promise.reject(new Error("A partida local só está disponível no aplicativo instalado."));
    return NativeEngine.playControlledMatch({ matchId, decision });
  },

  async saveCareer(state: LocalCareerState) {
    await writeLocalGameState(state);
  },
};
