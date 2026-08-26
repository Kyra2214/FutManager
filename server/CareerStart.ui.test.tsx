/** @vitest-environment jsdom */
import React, { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  catalog: vi.fn(),
  mutate: vi.fn(),
  invalidate: vi.fn(),
  mutationOptions: undefined as { onSuccess?: () => void } | undefined,
  mutationError: null as Error | null,
}));

vi.mock("@/lib/trpc", () => ({
  trpc: {
    useUtils: () => ({ career: { current: { invalidate: mocks.invalidate } } }),
    career: {
      catalog: { useQuery: mocks.catalog },
      start: { useMutation: (options: { onSuccess?: () => void }) => {
        mocks.mutationOptions = options;
        return { mutate: mocks.mutate, isPending: false, error: mocks.mutationError };
      } },
    },
  },
}));

import CareerStart from "../client/src/pages/CareerStart";

const club = { entityId: 7, name: "Clube Exemplo", mappingStatus: "COMPLETE", assetUrl: "/engine-assets/escudos/clubes/exemplo.png", assetKind: "crest" as const };
const selection = { entityId: 4, name: "Argentina", mappingStatus: "SOURCE_NOT_PROVIDED", assetUrl: "/engine-assets/selecoes/camisas/ARG.png", assetKind: "kit" as const };

function Harness() {
  const [started, setStarted] = useState(false);
  return started ? <div>Dashboard liberado</div> : <CareerStart onStarted={() => setStarted(true)} />;
}

describe("CareerStart UI", () => {
  beforeEach(() => {
    mocks.mutationError = null;
    mocks.invalidate.mockReset();
    mocks.mutate.mockReset();
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
    await user.click(screen.getByRole("button", { name: /Clube Exemplo/i }));
    await user.click(screen.getByRole("button", { name: /Começar carreira/i }));

    expect(mocks.mutate).toHaveBeenCalledWith(expect.objectContaining({ managerName: "Ana", targetType: "club", targetId: 7 }));
    expect(mocks.invalidate).toHaveBeenCalled();
    expect(screen.getByText("Dashboard liberado")).toBeTruthy();
  });

  it("mostra camisa e aviso honesto quando a seleção não possui escudo de origem", async () => {
    const user = userEvent.setup();
    render(<CareerStart onStarted={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: /Seleção/i }));

    expect(screen.getByRole("button", { name: /Argentina/i })).toBeTruthy();
    expect(screen.getByText("Escudo da seleção não fornecido; camisa disponível")).toBeTruthy();
  });

  it("exibe o erro retornado pela mutation", () => {
    mocks.mutationError = new Error("ACTIVE_CAREER_EXISTS");
    render(<CareerStart onStarted={vi.fn()} />);
    expect(screen.getByText("Já existe uma carreira ativa neste estado.")).toBeTruthy();
  });
});
