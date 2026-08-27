import { describe, expect, it } from "vitest";
import { isOfflineNativeRuntime } from "./localStore";

describe("offline runtime", () => {
  it("does not report the browser preview as native SQLite runtime", () => {
    expect(isOfflineNativeRuntime()).toBe(false);
  });
});
