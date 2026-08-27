import {
  isOfflineNativeRuntime,
  readLocalGameState,
  writeLocalGameState,
} from "./localStore";

export type LocalCareerState = Record<string, unknown>;

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

  async saveCareer(state: LocalCareerState) {
    await writeLocalGameState(state);
  },
};
