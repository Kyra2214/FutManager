/** @vitest-environment jsdom */
import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  useUtils: vi.fn(), summary: vi.fn(), catalog: vi.fn(), departmentOffers: vi.fn(), workspace: vi.fn(), trainingDepartments: vi.fn(), trainingDevelopment: vi.fn(), health: vi.fn(), hire: vi.fn(), upgradeDepartment: vi.fn(), toastSuccess: vi.fn(), toastError: vi.fn(),
}));

vi.mock("@/lib/trpc", () => ({ trpc: {
  useUtils: mocks.useUtils,
  club: { workspace: { useQuery: mocks.workspace } },
  staffMarket: {
    summary: { useQuery: mocks.summary },
    catalog: { useQuery: mocks.catalog },
    departmentOffers: { useQuery: mocks.departmentOffers },
    trainingDepartments: { useQuery: mocks.trainingDepartments },
    trainingDevelopment: { useQuery: mocks.trainingDevelopment },
    health: { useQuery: mocks.health },
    hire: { useMutation: mocks.hire },
    upgradeDepartment: { useMutation: mocks.upgradeDepartment },
  },
} }));
vi.mock("sonner", () => ({ toast: { success: mocks.toastSuccess, error: mocks.toastError } }));

import { StaffEconomyPanel } from "../client/src/components/StaffEconomyPanel";

const economy = {
  cash: 51600900, initial_cash: 51600900, weekly_player_payroll: 1323100,
  weekly_staff_payroll: 0, weekly_department_maintenance: 0, weekly_total: 1323100,
  team_power: 99.6, country_factor: 1.02,
};

describe("StaffEconomyPanel", () => {
  const hireMutate = vi.fn();
  const departmentMutate = vi.fn();
  let hireOptions: { onSuccess?: (result: { name: string; weekly_salary: number }) => void } | undefined;
  let departmentOptions: { onSuccess?: (result: { department: string; label: string; target_level: number; completion_at: string; duration_weeks: number }) => void } | undefined;
  const invalidates = { summary: vi.fn(), catalog: vi.fn(), departments: vi.fn(), workspace: vi.fn() };

  beforeEach(() => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    mocks.summary.mockReturnValue({ data: economy, isLoading: false });
    mocks.catalog.mockReturnValue({ data: [{ staff_id: 7, name: "Dra. Renata Moura", role: "medico", age: 44, experience: 100, reputation: 80, level: 8, potential: 78, specialization: "medicina esportiva", weekly_salary: 8277 }], isLoading: false });
    mocks.departmentOffers.mockReturnValue({ data: [{ department: "medicina", label: "Medicina", target_level: 1, cost: 162235, maintenance: 2438, capacity: 10 }], isLoading: false });
    mocks.workspace.mockReturnValue({ data: { staff: { members: [], averageLevel: 0, history: [], departments: [] } }, isLoading: false, error: null });
    mocks.trainingDepartments.mockReturnValue({ data: [], isLoading: false });
    mocks.trainingDevelopment.mockReturnValue({ data: [], isLoading: false });
    mocks.health.mockReturnValue({ data: [], isLoading: false });
    mocks.hire.mockImplementation((options) => { hireOptions = options; return { mutate: hireMutate, isPending: false }; });
    mocks.upgradeDepartment.mockImplementation((options) => { departmentOptions = options; return { mutate: departmentMutate, isPending: false }; });
    mocks.useUtils.mockReturnValue({ staffMarket: { summary: { invalidate: invalidates.summary }, catalog: { invalidate: invalidates.catalog }, departmentOffers: { invalidate: invalidates.departments } }, club: { workspace: { invalidate: invalidates.workspace } } });
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    vi.restoreAllMocks();
    hireOptions = undefined;
    departmentOptions = undefined;
  });

  it("mostra a reserva de 39 semanas e envia a contratação pelo contrato tRPC", () => {
    render(<StaffEconomyPanel mode="market" onNavigateToMarket={vi.fn()} />);
    expect(screen.getByText(/39 semanas \(3\/4 da temporada\)/)).toBeTruthy();
    expect(screen.getByText("Dra. Renata Moura")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Contratar" }));
    expect(hireMutate).toHaveBeenCalledWith({ staffId: 7 });
  });

  it("envia a evolução do departamento pelo contrato tRPC", () => {
    render(<StaffEconomyPanel mode="ct" onNavigateToMarket={vi.fn()} />);
    expect(screen.getByText(/medicina/i)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Comprar" }));
    expect(departmentMutate).toHaveBeenCalledWith({ department: "medicina" });
  });

  it("invalida os dados financeiros e estruturais após a mutation confirmada", async () => {
    render(<StaffEconomyPanel mode="market" onNavigateToMarket={vi.fn()} />);
    hireOptions?.onSuccess?.({ name: "Dra. Renata Moura", weekly_salary: 8277 });
    expect(mocks.toastSuccess).toHaveBeenCalledWith(expect.stringContaining("contratado"));
    expect(invalidates.summary).toHaveBeenCalledTimes(1);
    expect(invalidates.catalog).toHaveBeenCalledTimes(1);
    expect(invalidates.departments).toHaveBeenCalledTimes(1);
    expect(invalidates.workspace).toHaveBeenCalledTimes(1);

    cleanup();
    render(<StaffEconomyPanel mode="ct" onNavigateToMarket={vi.fn()} />);
    departmentOptions?.onSuccess?.({ department: "medicina", label: "Medicina", target_level: 1, completion_at: "2026-01-15", duration_weeks: 1 });
    expect(mocks.toastSuccess).toHaveBeenCalledWith(expect.stringContaining("entrou em obras"));
    await waitFor(() => expect(screen.getByText(/OBRA EM ANDAMENTO/)).toBeTruthy());
    expect(screen.getByText(/15\/01\/2026/)).toBeTruthy();
    expect(invalidates.summary).toHaveBeenCalledTimes(2);
    expect(invalidates.catalog).toHaveBeenCalledTimes(2);
    expect(invalidates.departments).toHaveBeenCalledTimes(2);
    expect(invalidates.workspace).toHaveBeenCalledTimes(2);
  });

  it.each([1024, 375])("reflete no painel em viewport %ipx os dados retornados após refetch", (viewport) => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: viewport });
    const { rerender } = render(<StaffEconomyPanel mode="market" onNavigateToMarket={vi.fn()} />);
    expect(screen.getByText("Dra. Renata Moura")).toBeTruthy();
    expect(screen.getAllByText(/1\.323\.100/).length).toBeGreaterThan(0);
    hireOptions?.onSuccess?.({ name: "Dra. Renata Moura", weekly_salary: 8277 });
    mocks.summary.mockReturnValue({ data: { ...economy, weekly_staff_payroll: 8277, weekly_total: 1331377 }, isLoading: false });
    mocks.catalog.mockReturnValue({ data: [], isLoading: false });
    rerender(<StaffEconomyPanel mode="market" onNavigateToMarket={vi.fn()} />);
    expect(screen.getAllByText(/1\.331\.377/).length).toBeGreaterThan(0);
    expect(screen.getByText("Não há profissional disponível nessa função.")).toBeTruthy();
  });
});
