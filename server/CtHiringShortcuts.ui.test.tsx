/** @vitest-environment jsdom */
import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ workspace: vi.fn(), toast: vi.fn() }));

vi.mock("@/lib/trpc", () => ({ trpc: { club: { workspace: { useQuery: mocks.workspace } } } }));
vi.mock("sonner", () => ({ toast: mocks.toast }));

import { StructurePage } from "../client/src/pages/Home";

const emptyWorkspace = {
  source: { available: true, message: "Estado conectado." },
  club: { clubId: 3280, name: "Flamengo", stadiumName: "Maracanã" },
  squad: { total: 32, starters: 19, reserves: 13, injured: 0, players: [] },
  stadium: { name: "Maracanã", capacity: null, level: null, status: null, source: "TEAM_RECORD" },
  training: { available: false, message: "Sem CT persistido." },
  staff: { members: [], departments: [], roleCounts: {} },
  health: { activeInjuries: [], count: 0 },
  scouting: { missions: [], opportunities: 0, reports: 0 },
};

describe("Atalhos de contratação do CT", () => {
  afterEach(() => {
    cleanup();
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 1024 });
  });

  beforeEach(() => {
    mocks.workspace.mockReturnValue({ data: emptyWorkspace, isLoading: false });
    mocks.toast.mockReset();
  });

  it.each([
    ["Comissão técnica", "Comissão técnica ainda não possui registros. Vá ao Mercado para contratar."],
    ["Médicos", "Médicos ainda não possui registros. Vá ao Mercado para contratar."],
    ["Auxiliares", "Auxiliares ainda não possui registros. Vá ao Mercado para contratar."],
    ["Departamentos", "Departamentos ainda não possui registros. Vá ao Mercado para contratar."],
  ])("orienta %s ao Mercado quando não há registros", (label, message) => {
    const onSectionChange = vi.fn();
    render(<StructurePage section="ct" onSectionChange={onSectionChange} />);

    const trigger = screen.getByText(label, { exact: true }).closest("button");
    expect(trigger).not.toBeNull();
    fireEvent.click(trigger!);

    expect(mocks.toast).toHaveBeenCalledWith(message);
    expect(onSectionChange).toHaveBeenCalledWith("mercado");
  });

  it("mantém os quatro atalhos funcionais em condição de viewport móvel", () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 375 });
    const onSectionChange = vi.fn();
    render(<StructurePage section="ct" onSectionChange={onSectionChange} />);

    ["Comissão técnica", "Médicos", "Auxiliares", "Departamentos"].forEach((label) => {
      const trigger = screen.getByText(label, { exact: true }).closest("button");
      fireEvent.click(trigger!);
    });

    expect(mocks.toast).toHaveBeenCalledTimes(4);
    expect(onSectionChange).toHaveBeenCalledTimes(4);
    expect(onSectionChange).toHaveBeenNthCalledWith(4, "mercado");
  });
});
