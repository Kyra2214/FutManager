/** @vitest-environment jsdom */
import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  restore: vi.fn(),
  invalidate: vi.fn(),
}));

vi.mock("@/_core/hooks/useAuth", () => ({ useAuth: () => ({ isAuthenticated: true }) }));
vi.mock("sonner", () => ({ toast: vi.fn() }));
vi.mock("@/lib/trpc", () => ({
  trpc: {
    useUtils: () => ({
      career: { current: { invalidate: mocks.invalidate } },
      operations: { snapshots: { list: { invalidate: mocks.invalidate }, audit: { invalidate: mocks.invalidate } }, simulation: { progress: { invalidate: mocks.invalidate }, metrics: { invalidate: mocks.invalidate } }, finance: { monthlyClose: { invalidate: mocks.invalidate } } },
    }),
    career: { current: { useQuery: () => ({ data: { started: true }, isLoading: false }) } },
    operations: {
      snapshots: {
        list: { useQuery: () => ({ data: { items: [{ snapshot_id: 1, career_id: 9, created_at: "2027-01-01", engine_version: "v4" }, { snapshot_id: 2, career_id: 9, created_at: "2027-01-02", engine_version: "v4" }] }, isLoading: false }) },
        audit: { useQuery: () => ({ data: { items: [] }, isLoading: false }) },
        compare: { useQuery: ({ leftId, rightId }: { leftId: number; rightId: number }, options: { enabled: boolean }) => options.enabled ? { data: { left_id: leftId, right_id: rightId, left_hash: "a".repeat(64), right_hash: "b".repeat(64), same_career: true, identical: false, read_only: true } } : { data: undefined } },
        create: { useMutation: () => ({ mutate: vi.fn(), isPending: false }) },
        restore: { useMutation: () => ({ mutate: mocks.restore, isPending: false }) },
      },
      simulation: {
        progress: { useQuery: () => ({ data: { status: "IDLE", processed: 0 }, error: null }) },
        metrics: { useQuery: () => ({ data: { throughput_estimate: 0, checkpoints: 0 } }) },
        batch: { useMutation: () => ({ mutate: vi.fn(), isPending: false }) },
        resume: { useMutation: () => ({ mutate: vi.fn(), isPending: false }) },
      },
      finance: { monthlyClose: { useQuery: () => ({ data: { net: 0, categories: [] }, error: null }) } },
    },
  },
}));

import { OperationsPanel } from "../client/src/components/OperationsPanel";

describe("OperationsPanel snapshots", () => {
  afterEach(() => cleanup());
  beforeEach(() => { mocks.restore.mockReset(); });

  it("compara dois snapshots lado a lado sem mutar o motor", async () => {
    const user = userEvent.setup();
    render(<OperationsPanel />);
    await user.click(screen.getAllByLabelText("A")[0]);
    await user.click(screen.getAllByLabelText("B")[1]);
    expect(screen.getByText("Comparação somente leitura")).toBeTruthy();
    expect(mocks.restore).not.toHaveBeenCalled();
  });

  it("exige seleção de campo e confirmação antes da restauração", async () => {
    const user = userEvent.setup();
    render(<OperationsPanel />);
    await user.click(screen.getAllByLabelText("B")[1]);
    await user.click(screen.getByRole("button", { name: /Preparar restauração/i }));
    expect(screen.getByRole("alertdialog")).toBeTruthy();
    expect(mocks.restore).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: /Confirmar restauração/i }));
    expect(mocks.restore).toHaveBeenCalledWith({ snapshotId: 2, fields: ["current_club_id"] });
  });
});
