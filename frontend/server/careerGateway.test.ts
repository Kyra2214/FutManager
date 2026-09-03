import { describe, expect, it, vi } from "vitest";

const { execFileSyncMock } = vi.hoisted(() => ({ execFileSyncMock: vi.fn() }));

vi.mock("node:child_process", async () => ({
  ...(await vi.importActual<typeof import("node:child_process")>("node:child_process")),
  execFileSync: execFileSyncMock,
}));

import {
  getCurrentCareer,
  listCareerTargets,
  listWorldCountries,
  runCareerGatewayAction,
  startCareer,
} from "./careerGateway";

describe("careerGateway", () => {
  it("executa a ação current pelo processo Python e desserializa o retorno", () => {
    execFileSyncMock.mockReturnValueOnce(JSON.stringify({ ok: true, started: false }));

    expect(getCurrentCareer("/tmp/game.db")).toMatchObject({ ok: true, started: false });
    expect(execFileSyncMock).toHaveBeenCalledWith(
      "python3",
      expect.arrayContaining(["current", "--database", "/tmp/game.db"]),
      expect.objectContaining({ encoding: "utf8", timeout: 60_000 }),
    );
  });

  it("monta corretamente catálogo de clubes e países", () => {
    execFileSyncMock
      .mockReturnValueOnce(JSON.stringify({
        ok: true,
        items: [{ entityId: 7, name: "Palmeiras", countryId: 29, mappingStatus: "COMPLETE", assetUrl: null, assetKind: null }],
      }))
      .mockReturnValueOnce(JSON.stringify({
        ok: true,
        items: [{ countryId: 29, name: "Brasil", code: "BR", clubCount: 20, firstDivisionClubCount: 20, firstDivisionName: "Série A" }],
      }));

    expect(listCareerTargets("club", "Palmeiras", 8, "/tmp/game.db")[0]).toMatchObject({ entityId: 7, name: "Palmeiras" });
    expect(listWorldCountries("Brasil", 8, "/tmp/game.db")[0]).toMatchObject({ countryId: 29, name: "Brasil" });
  });

  it("envia todos os campos da criação de carreira ao gateway", () => {
    execFileSyncMock.mockReturnValueOnce(JSON.stringify({ ok: true, started: true, target_id: 7 }));

    expect(startCareer({
      managerName: "Ana",
      nationality: "BR",
      age: 31,
      careerName: "Carreira Ana",
      targetType: "club",
      targetId: 7,
      selectedCountryIds: [29, 65],
    }, "/tmp/game.db")).toMatchObject({ started: true, target_id: 7 });

    expect(execFileSyncMock.mock.calls[0][1]).toEqual(expect.arrayContaining([
      "start",
      "--database",
      "/tmp/game.db",
    ]));
    expect(JSON.parse(String(execFileSyncMock.mock.calls[0][2]?.input))).toMatchObject({
      manager_name: "Ana",
      nationality: "BR",
      age: 31,
      career_name: "Carreira Ana",
      target_type: "club",
      target_id: 7,
      selected_country_ids: [29, 65],
    });
  });

  it("converte falha do gateway em erro público estável", () => {
    execFileSyncMock.mockReturnValueOnce(JSON.stringify({ ok: false, error: "CLUB_NOT_FOUND" }));

    expect(() => runCareerGatewayAction("current", {}, "/tmp/game.db"))
      .toThrow("CLUB_NOT_FOUND");
  });

  it("converte exceção do processo em CAREER_GATEWAY_UNAVAILABLE", () => {
    execFileSyncMock.mockImplementationOnce(() => {
      throw new Error("python crashed");
    });

    expect(() => runCareerGatewayAction("current", {}, "/tmp/game.db"))
      .toThrow("CAREER_GATEWAY_UNAVAILABLE");
  });
});
