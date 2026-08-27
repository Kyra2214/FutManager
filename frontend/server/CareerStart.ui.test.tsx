/** @vitest-environment jsdom */
import React, { useState } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  catalog: vi.fn(),
  parallelPreview: vi.fn(),
  mutate: vi.fn(),
  invalidate: vi.fn(),
  mutationOptions: undefined as { onSuccess?: () => void } | undefined,
  mutationError: null as Error | null,
  current: { started: false } as { started: boolean; careerName?: string; targetName?: string; targetType?: "club" | "selection" },
}));

vi.mock("@/lib/trpc", () => ({
  trpc: {
    useUtils: () => ({ career: { current: { invalidate: mocks.invalidate } } }),
    career: {
      catalog: { useQuery: mocks.catalog },
      worldCountries: { useQuery: () => ({ data: { items: [{ countryId: 29, name: "Brasil", code: "BRA", clubCount: 10 }] }, isLoading: false, isError: false }) },
      current: { useQuery: () => ({ data: mocks.current, isLoading: false }) },
      parallelPreview: { useQuery: mocks.parallelPreview },
      start: { useMutation: (options: { onSuccess?: () => void }) => {
        mocks.mutationOptions = options;
        return { mutate: mocks.mutate, isPending: false, error: mocks.mutationError };
      } },
    },
  },
}));

import CareerStart from "../client/src/pages/CareerStart";

const club = { entityId: 7, name: "Clube Exemplo", countryId: 29, mappingStatus: "COMPLETE", assetUrl: "/engine-assets/escudos/clubes/exemplo.png", assetKind: "crest" as const };
const selection = { entityId: 4, name: "Argentina", mappingStatus: "SOURCE_NOT_PROVIDED", assetUrl: "/engine-assets/selecoes/camisas/ARG.png", assetKind: "kit" as const };

function Harness() {
  const [started, setStarted] = useState(false);
  return started ? <div>Dashboard liberado</div> : <CareerStart onStarted={() => setStarted(true)} />;
}

describe("CareerStart UI", () => {
  afterEach(() => cleanup());
  beforeEach(() => {
    mocks.mutationError = null;
    mocks.current = { started: false };
    mocks.invalidate.mockReset();
    mocks.mutate.mockReset();
    mocks.parallelPreview.mockReturnValue({ data: null, isLoading: false, isError: false });
    mocks.catalog.mockImplementation(({ targetType }: { targetType: "club" | "selection" }) => ({
      data: targetType === "club" ? [club] : [selection],
      isLoading: false,
      isError: false,
    }));
    mocks.mutate.mockImplementation(() => mocks.mutationOptions?.onSuccess?.());
  });

  it("seleciona um clube, inicia a carreira e transita para o dashboard", async () => {
    const user = userEvent.setup();
    render(<Harness />);
    await user.type(screen.getByPlaceholderText("Como o manager será chamado?"), "Ana");
    await user.click(screen.getByRole("button", { name: /Brasil/i }));
    await user.click(screen.getByRole("button", { name: /Clube Exemplo/i }));
    await user.click(screen.getByRole("button", { name: /Começar carreira/i }));

    expect(mocks.mutate).toHaveBeenCalledWith(expect.objectContaining({ managerName: "Ana", targetType: "club", targetId: 7, selectedCountryIds: [29] }));
    expect(mocks.invalidate).toHaveBeenCalled();
    expect(screen.getByText("Dashboard liberado")).toBeTruthy();
  });

  it("bloqueia o início quando nenhuma liga foi selecionada", async () => {
    const user = userEvent.setup();
    render(<CareerStart onStarted={vi.fn()} />);
    await user.type(screen.getByPlaceholderText("Como o manager será chamado?"), "Ana");
    await user.click(screen.getByRole("button", { name: /Clube Exemplo/i }));
    expect((screen.getByRole("button", { name: /Começar carreira/i }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByText("Escolha pelo menos uma liga para liberar o início da carreira.")).toBeTruthy();
  });

  it("mostra camisa e aviso honesto quando a seleção não possui escudo de origem", async () => {
    const user = userEvent.setup();
    render(<CareerStart onStarted={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: /Seleção/i }));

    expect(screen.getByRole("button", { name: /Argentina/i })).toBeTruthy();
    expect(screen.getByText("Escudo da seleção não fornecido; camisa disponível")).toBeTruthy();
  });

  it("oferece continuar o save ativo ou criar um novo save", async () => {
    const user = userEvent.setup();
    mocks.current = { started: true, careerName: "Temporada 2026", targetName: "Flamengo", targetType: "club" };
    const onContinue = vi.fn();
    render(<CareerStart onStarted={vi.fn()} onContinue={onContinue} />);
    expect(screen.getByText("Temporada 2026")).toBeTruthy();
    await user.click(screen.getByRole("button", { name: /Continuar save/i }));
    expect(onContinue).toHaveBeenCalledOnce();
    await user.type(screen.getByPlaceholderText("Como o manager será chamado?"), "Novo Manager");
    await user.click(screen.getByRole("button", { name: /Brasil/i }));
    await user.click(screen.getByRole("button", { name: /Clube Exemplo/i }));
    await user.click(screen.getByRole("button", { name: /Começar carreira/i }));
    expect(mocks.mutate).toHaveBeenCalledWith(expect.objectContaining({ managerName: "Novo Manager", targetId: 7, selectedCountryIds: [29] }));
  });
});

  it("renderiza a prévia oficial dos clubes distribuídos nas quatro divisões", () => {
    mocks.parallelPreview.mockReturnValue({
      data: {
        total_clubs: 4,
        country_count: 1,
        division_count: 4,
        seed: "seed-teste",
        target_division: 4,
        read_only: true,
        divisions: [1, 2, 3, 4].map((division) => ({ division, clubs: [{ club_id: division, origin_country_id: 29, name: `Clube ${division}` }] })),
      },
      isLoading: false,
      isError: false,
    });
    render(<CareerStart onStarted={vi.fn()} />);
    expect(screen.getByText("4 clubes · 4 divisões")).toBeTruthy();
    expect(screen.getByText("Clube 1")).toBeTruthy();
    expect(screen.getByText("Clube 4")).toBeTruthy();
    expect(screen.getByText("Sorteio persistirá no save · seed seed-teste")).toBeTruthy();
  });
