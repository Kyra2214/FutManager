// @vitest-environment jsdom
import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  advance: vi.fn(),
  play: vi.fn(),
}));

vi.mock("@/lib/trpc", () => ({
  trpc: {
    useUtils: () => ({
      career: { current: { invalidate: vi.fn() } },
      matches: { dashboard: { invalidate: vi.fn() } },
      events: { list: { invalidate: vi.fn() } },
    }),
    club: {
      workspace: { useQuery: () => ({ data: { squad: { players: [{ playerId: 1, name: "Atacante A", position: "Atacante", status: "Titular", category: "profissional" }, { playerId: 2, name: "Reserva B", position: "Meia", status: "Reserva", category: "profissional" }] } } }) },
    },
    matches: {
      dashboard: { useQuery: () => ({ data: {
        selectedCompetitionId: 12,
        selectedCompetition: { competitionId: 12, name: "Liga FutManager", seasonYear: 2026 },
        competitions: [{ competitionId: 12, name: "Liga FutManager", type: "league", format: "pontos corridos", status: "ativa", playedMatches: 0, scheduledFixtures: 1, seasonYear: 2026 }],
        controlledClub: { clubId: 7, name: "Clube Exemplo" },
        upcomingFixtures: [{ matchId: 101, scheduledAt: "2026-08-30T12:00:00Z", round: 1, homeClub: { clubId: 7, name: "Clube Exemplo" }, awayClub: { clubId: 8, name: "Clube Visitante" } }],
        recentResults: [],
        standings: [],
        source: { available: true, message: "Calendário atualizado" },
      }, isLoading: false, error: null }) },
      travelPreview: { useQuery: () => ({ data: undefined, isLoading: false, error: null }) },
      travelSummary: { useQuery: () => ({ data: undefined, isLoading: false, error: null }) },
      playControlled: { useMutation: () => ({ mutate: mocks.play, isPending: false }) },
    },
    events: { list: { useQuery: () => ({ data: { items: [] }, isLoading: false, error: null }) } },
    career: { advanceWeek: { useMutation: () => ({ mutate: mocks.advance, isPending: false }) } },
  },
}));

import { MatchesPage } from "../client/src/pages/Home";

describe("MatchesPage — avanço da carreira", () => {
  afterEach(() => {
    cleanup();
    mocks.advance.mockReset();
    mocks.play.mockReset();
  });

  it("envia o avanço semanal pelo contrato da carreira", () => {
    render(<MatchesPage />);

    fireEvent.click(screen.getByRole("button", { name: "Avançar semana" }));

    expect(mocks.advance).toHaveBeenCalledWith({});
    fireEvent.pointerDown(screen.getByRole("button", { name: "Iniciar partida" }));
    expect(mocks.play).not.toHaveBeenCalled();
    expect(screen.getByText("AO VIVO")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Pausar jogo" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /simula/i })).toBeNull();
  });
});
