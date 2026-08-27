// @vitest-environment jsdom
import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  advance: vi.fn(),
  goToMatch: vi.fn(),
  play: vi.fn(),
    openMatch: vi.fn(),
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
    career: { advanceWeek: { useMutation: () => ({ mutate: mocks.advance, isPending: false }) }, advanceUntilMatch: { useMutation: () => ({ mutate: mocks.goToMatch, isPending: false }) } },
  },
}));

import { MatchesPage } from "../client/src/pages/Home";
import { InteractiveMatchCenter } from "../client/src/components/InteractiveMatchCenter";

describe("MatchesPage — avanço da carreira", () => {
  afterEach(() => {
    cleanup();
    mocks.advance.mockReset();
    mocks.play.mockReset();
    mocks.openMatch.mockReset();
  });

  it("envia o avanço semanal pelo contrato da carreira", () => {
    render(<MatchesPage onOpenMatch={mocks.openMatch} />);

    fireEvent.click(screen.getAllByRole("button", { name: "Ir para partida" })[0]);
    expect(mocks.goToMatch).toHaveBeenCalledWith({ matchId: 101 });
    expect(mocks.openMatch).not.toHaveBeenCalled();
    expect(screen.getByText("Campo, placar e decisões. Só isso.")).toBeTruthy();
    expect(screen.queryByText("TRANSMISSÃO INTERATIVA")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Avançar semana" }));

    expect(mocks.advance).toHaveBeenCalledWith({});
    expect(screen.queryByRole("button", { name: /simula/i })).toBeNull();
  });
});


describe("InteractiveMatchCenter — modo dedicado", () => {
  it("inicia a transmissão dentro da tela exclusiva", () => {
    render(<InteractiveMatchCenter match={{ matchId: 101, round: 1, scheduledAt: "2026-08-30T12:00:00Z", homeClub: { clubId: 7, name: "Clube Exemplo" }, awayClub: { clubId: 8, name: "Clube Visitante" } }} players={[{ playerId: 1, name: "Atacante A", position: "Atacante", status: "Titular", category: "profissional" }]} />);
    fireEvent.pointerDown(screen.getByTestId("start-match-button"));
    expect(screen.getByText("AO VIVO")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Pausar jogo" })).toBeTruthy();
  });
});
