import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { SolubilityTableOverlay } from "@/components/tests/SolubilityTableOverlay";

describe("SolubilityTableOverlay", () => {
  it("opens the solubility reference dialog", async () => {
    render(<SolubilityTableOverlay />);

    await userEvent.click(
      screen.getByRole("button", { name: "Таблица растворимости" }),
    );

    expect(
      screen.getByRole("dialog", { name: "Таблица растворимости" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Растворимость кислот, солей и оснований в воде/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Ряд активности металлов/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Li")).toBeInTheDocument();
    expect(screen.getByText("OH⁻")).toBeInTheDocument();
  });

  it("closes on Escape", async () => {
    render(<SolubilityTableOverlay />);

    const trigger = screen.getByRole("button", {
      name: "Таблица растворимости",
    });
    await userEvent.click(trigger);

    await userEvent.keyboard("{Escape}");

    expect(
      screen.queryByRole("dialog", { name: "Таблица растворимости" }),
    ).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();
  });

  it("color-codes soluble cells", async () => {
    render(<SolubilityTableOverlay />);

    await userEvent.click(
      screen.getByRole("button", { name: "Таблица растворимости" }),
    );

    const solubleCells = document.querySelectorAll(".chem-solubility-p");
    expect(solubleCells.length).toBeGreaterThan(0);
  });
});
