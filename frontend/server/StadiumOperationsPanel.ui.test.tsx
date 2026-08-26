/** @vitest-environment jsdom */
import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ useUtils: vi.fn(), summary: vi.fn(), preview: vi.fn(), ticketPreview: vi.fn(), fanSegments: vi.fn(), socialTimeline: vi.fn(), bootstrap: vi.fn(), upgrade: vi.fn(), ticket: vi.fn(), advance: vi.fn(), toastSuccess: vi.fn(), toastError: vi.fn() }));
vi.mock("@/lib/trpc", () => ({ trpc: {
  useUtils: mocks.useUtils,
  stadium: { summary: { useQuery: mocks.summary }, preview: { useQuery: mocks.preview }, ticketPricePreview: { useQuery: mocks.ticketPreview }, fanSegments: { useQuery: mocks.fanSegments }, socialTimeline: { useQuery: mocks.socialTimeline }, bootstrap: { useMutation: mocks.bootstrap }, upgrade: { useMutation: mocks.upgrade }, ticketPrice: { useMutation: mocks.ticket }, advanceWeek: { useMutation: mocks.advance } },
} }));
vi.mock("sonner", () => ({ toast: { success: mocks.toastSuccess, error: mocks.toastError } }));
import { StadiumOperationsPanel } from "../client/src/components/StadiumOperationsPanel";

const summary = {
  initialized: true,
  stadium: { stadium_id: 1, name: "Maracanã", base_capacity: 12000, capacity: 14250, maintenance: 5400, matchday_quality: 10, components: [
    { component: "arquibancada" as const, level: 2, next_level: 3, upgrade_cost: 220000, maintenance: 2150 },
    { component: "campo" as const, level: 1, next_level: 2, upgrade_cost: 95000, maintenance: 900 },
    { component: "estrutura" as const, level: 1, next_level: 2, upgrade_cost: 130000, maintenance: 1150 },
    { component: "equipes" as const, level: 1, next_level: 2, upgrade_cost: 84000, maintenance: 1050 },
  ] },
  fan_base: { size: 22000, satisfaction: 52, engagement: 50, interest: 51 },
  reputation: { sporting: 62, commercial: 48, national: 61 }, ticket_price: 42,
  attendance: [{ match_id: 7, expected_attendance: 13000, actual_attendance: 12600, ticket_price: 42, revenue: 529200 }],
};

describe("StadiumOperationsPanel", () => {
  const mutations = { bootstrap: vi.fn(), upgrade: vi.fn(), ticket: vi.fn(), advance: vi.fn() };
  const invalidates = { stadium: vi.fn(), workspace: vi.fn(), sponsor: vi.fn(), matches: vi.fn(), economy: vi.fn(), offers: vi.fn() };
  beforeEach(() => {
    mocks.summary.mockReturnValue({ data: summary, isLoading: false });
    mocks.preview.mockReturnValue({ data: { from_level: 2, target_level: 3, cash_after: 500000, maintenance_before: 5400, maintenance_after: 6150, cash_sufficient: true }, isLoading: false });
    mocks.ticketPreview.mockReturnValue({ data: { rejection_risk: 8, expected_attendance: 12000, expected_revenue: 504000 }, isLoading: false });
    mocks.fanSegments.mockReturnValue({ data: { segments: { local: 14300, national: 5500, international: 2200 } }, isLoading: false });
    mocks.socialTimeline.mockReturnValue({ data: { items: [] }, isLoading: false });
    mocks.bootstrap.mockReturnValue({ mutate: mutations.bootstrap, isPending: false });
    mocks.upgrade.mockReturnValue({ mutate: mutations.upgrade, isPending: false });
    mocks.ticket.mockReturnValue({ mutate: mutations.ticket, isPending: false });
    mocks.advance.mockReturnValue({ mutate: mutations.advance, isPending: false });
    mocks.useUtils.mockReturnValue({ stadium: { summary: { invalidate: invalidates.stadium } }, club: { workspace: { invalidate: invalidates.workspace } }, sponsorship: { summary: { invalidate: invalidates.sponsor }, offers: { invalidate: invalidates.offers } }, matches: { dashboard: { invalidate: invalidates.matches } }, staffMarket: { summary: { invalidate: invalidates.economy } } });
  });
  afterEach(() => { cleanup(); vi.clearAllMocks(); });

  it.each([1024, 375])("mostra estádio, componentes e bilheteria no viewport %ipx", (viewport) => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: viewport });
    render(<StadiumOperationsPanel />);
    expect(screen.getByText("Maracanã")).toBeTruthy();
    expect(screen.getByText("Arquibancada")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Avançar uma semana/i })).toBeTruthy();
    expect(screen.getByText("12.600")).toBeTruthy();
  });

  it("envia upgrade, preço e avanço semanal por tRPC", () => {
    render(<StadiumOperationsPanel />);
    fireEvent.click(screen.getAllByRole("button", { name: /Ver impacto/i })[0]);
    fireEvent.click(screen.getByRole("button", { name: "Confirmar evolução" }));
    fireEvent.click(screen.getByRole("button", { name: "Salvar preço" }));
    fireEvent.click(screen.getByRole("button", { name: /Avançar uma semana/i }));
    expect(mutations.upgrade).toHaveBeenCalledWith({ component: "arquibancada" });
    expect(mutations.ticket).toHaveBeenCalledWith({ basePrice: 42 });
    expect(mutations.advance).toHaveBeenCalledWith({});
  });

  it("oferece preparação explícita quando não há estádio econômico", () => {
    mocks.summary.mockReturnValue({ data: { ...summary, initialized: false, stadium: null }, isLoading: false });
    render(<StadiumOperationsPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Preparar estádio" }));
    expect(mutations.bootstrap).toHaveBeenCalledTimes(1);
  });
});
