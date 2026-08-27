/** @vitest-environment jsdom */
import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TableSkeleton } from "@/components/TableSkeleton";

describe("TableSkeleton", () => {
  it("renderiza uma tabela em carregamento com estrutura acessível", () => {
    render(<TableSkeleton rows={3} columns={4} />);
    expect(screen.getByRole("status", { name: "Carregando tabela" })).toBeTruthy();
    expect(screen.getAllByRole("status")[0].querySelectorAll("[data-slot='skeleton']")).toHaveLength(12);
  });
});
