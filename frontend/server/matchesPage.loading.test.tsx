import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/trpc", () => ({
  trpc: {
    matches: {
      dashboard: {
        useQuery: () => ({ data: undefined, error: null, isLoading: true }),
      },
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
