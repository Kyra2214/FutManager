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
  },
}));

import { MatchesPage } from "../client/src/pages/Home";

describe("MatchesPage em carregamento", () => {
  it.each([
    ["competicoes", "Lendo o estado esportivo"],
    ["tabela", "Consultando o estado oficial do motor"],
    ["calendario", "Consultando o estado oficial do motor"],
    ["resultados", "Consultando o estado oficial do motor"],
  ] as const)("mantém feedback explícito na visão %s", (initialView, expectedText) => {
    const markup = renderToStaticMarkup(<MatchesPage initialView={initialView} />);

    expect(markup).toContain(expectedText);
    expect(markup).toContain("consultando estado");
  });
});
