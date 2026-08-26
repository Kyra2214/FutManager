/** @vitest-environment jsdom */
import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ useUtils: vi.fn(), summary: vi.fn(), offers: vi.fn(), accept: vi.fn(), toastSuccess: vi.fn(), toastError: vi.fn() }));

vi.mock("@/lib/trpc", () => ({ trpc: {
  useUtils: mocks.useUtils,
  sponsorship: { summary: { useQuery: mocks.summary }, offers: { invalidate: vi.fn() }, accept: { useMutation: mocks.accept } },
} }));
vi.mock("sonner", () => ({ toast: { success: mocks.toastSuccess, error: mocks.toastError } }));

import { SponsorshipPanel } from "../client/src/components/SponsorshipPanel";

const commercial = {
  club_id: 3280,
  institutional_overall: 63.5,
  sponsor_stars: 4,
  institutional_profile: { squad_score: 92, ct_score: 0, stadium_score: 25, squad_available: true, ct_available: false, stadium_available: false },
  active_contract: null,
  offers: [{ offer_id: 9840, star_rating: 4, minimum_overall: 56, upfront_payment: 597518, weekly_payment: 147081, mission_bonus: 551555, contract_weeks: 6, status: "PENDING", name: "Alvorada", industry: "serviços", expires_season: 2026, expires_week: 3, source_overall: 63.5, source_stars: 4 }],
  missions: [],
};

describe("SponsorshipPanel", () => {
  let acceptOptions: { onSuccess?: (contract: { sponsor: string; upfront_payment: number }) => Promise<void> } | undefined;
  const acceptMutate = vi.fn();
  const invalidates = { summary: vi.fn(), offers: vi.fn(), workspace: vi.fn(), economy: vi.fn() };

  beforeEach(() => {
    mocks.summary.mockReturnValue({ data: commercial, isLoading: false });
    mocks.accept.mockImplementation((options) => { acceptOptions = options; return { mutate: acceptMutate, isPending: false }; });
    mocks.useUtils.mockReturnValue({ sponsorship: { summary: { invalidate: invalidates.summary }, offers: { invalidate: invalidates.offers } }, club: { workspace: { invalidate: invalidates.workspace } }, staffMarket: { summary: { invalidate: invalidates.economy } } });
  });
  afterEach(() => { cleanup(); vi.clearAllMocks(); acceptOptions = undefined; });

  it.each([1024, 375])("mostra overall, estrelas e proposta no viewport %ipx", (viewport) => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: viewport });
    render(<SponsorshipPanel />);
    expect(screen.getByText("63.5")).toBeTruthy();
    expect(screen.getByText("Alvorada")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Escolher patrocinador" })).toBeTruthy();
    expect(screen.getAllByText(/base preparatória/i)).toHaveLength(2);
  });

  it("envia a decisão pelo contrato tRPC e invalida os resumos associados", async () => {
    render(<SponsorshipPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Escolher patrocinador" }));
    expect(acceptMutate).toHaveBeenCalledWith({ offerId: 9840 });
    await acceptOptions?.onSuccess?.({ sponsor: "Alvorada", upfront_payment: 597518 });
    expect(mocks.toastSuccess).toHaveBeenCalledWith(expect.stringContaining("Alvorada"));
    expect(invalidates.summary).toHaveBeenCalledTimes(1);
    expect(invalidates.offers).toHaveBeenCalledTimes(1);
    expect(invalidates.workspace).toHaveBeenCalledTimes(1);
    expect(invalidates.economy).toHaveBeenCalledTimes(1);
  });

  it("renderiza contrato e missão retornados após o refetch", () => {
    mocks.summary.mockReturnValue({ data: { ...commercial, offers: [], active_contract: { contract_id: 77, sponsor_id: 7, name: "Alvorada", industry: "serviços", star_rating: 4, upfront_payment: 597518, weekly_payment: 147081, mission_bonus: 551555, end_season: 2026, end_week: 6, status: "ACTIVE" }, missions: [{ mission_id: 1, title: "Amplie o overall institucional", mission_type: "institutional_overall", target_value: 68, current_value: 63.5, reward: 551555, status: "ACTIVE", deadline_season: 2026, deadline_week: 6 }] }, isLoading: false });
    render(<SponsorshipPanel />);
    expect(screen.getByText(/patrocinador principal ativo/i)).toBeTruthy();
    expect(screen.getByText(/Amplie o overall institucional/)).toBeTruthy();
    expect(screen.getByText(/R\$\s?147\.081/)).toBeTruthy();
  });
});
