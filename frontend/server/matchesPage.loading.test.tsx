import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/trpc", () => ({
  trpc: {
    useUtils: () => ({ career: { current: { invalidate: vi.fn() } }, matches: { dashboard: { invalidate: vi.fn() } }, events: { list: { invalidate: vi.fn() } } }),
    career: {
      advanceWeek: { useMutation: () => ({ mutate: vi.fn(), isPending: false }) },
      advanceUntilMatch: { useMutation: () => ({ mutate: vi.fn(), isPending: false }) },
    },
    club: { workspace: { useQuery: () => ({ data: undefined, error: null, isLoading: true }) } },
    matches: {
      dashboard: {
        useQuery: () => ({ data: undefined, error: null, isLoading: true }),
      },
      playControlled: { useMutation: () => ({ mutate: vi.fn(), isPending: false }) },
    },
    events: {
      list: {
        useQuery: () => ({ data: { items: [], unread_count: 0 }, error: null, isLoading: true }),
      },
    },
  },
}));

import { MatchesPage } from "../client/src/pages/Home";

describe("MatchesPage em carregamento", () => {
  it.each([
    ["competicoes", "Atualizando a temporada"],
    ["tabela", "Atualizando a temporada"],
    ["calendario", "Atualizando a temporada"],
    ["resultados", "Atualizando a temporada"],
  ] as const)("mantém feedback explícito na visão %s", (initialView, expectedText) => {
    const markup = renderToStaticMarkup(<MatchesPage initialView={initialView} />);

    expect(markup).toContain(expectedText);
    expect(markup).toContain("atualizando calendário");
  });
});
