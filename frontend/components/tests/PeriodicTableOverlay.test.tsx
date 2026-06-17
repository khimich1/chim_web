import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { PeriodicTableOverlay } from "@/components/tests/PeriodicTableOverlay";

describe("PeriodicTableOverlay", () => {
  it("opens the periodic table dialog on button click", async () => {
    render(<PeriodicTableOverlay />);

    await userEvent.click(
      screen.getByRole("button", { name: "Таблица Менделеева" }),
    );

    const dialog = screen.getByRole("dialog", {
      name: "Таблица Менделеева",
    });
    expect(dialog).toBeInTheDocument();
    expect(
      screen.getByAltText(
        "Периодическая таблица химических элементов Менделеева",
      ),
    ).toHaveAttribute("src", "/images/mendeleev-periodic-table.png");
  });

  it("closes on Escape and returns focus to the trigger", async () => {
    render(<PeriodicTableOverlay />);

    const trigger = screen.getByRole("button", { name: "Таблица Менделеева" });
    await userEvent.click(trigger);

    expect(
      screen.getByRole("dialog", { name: "Таблица Менделеева" }),
    ).toBeInTheDocument();

    await userEvent.keyboard("{Escape}");

    expect(
      screen.queryByRole("dialog", { name: "Таблица Менделеева" }),
    ).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();
  });

  it("closes when clicking the backdrop", async () => {
    render(<PeriodicTableOverlay />);

    await userEvent.click(
      screen.getByRole("button", { name: "Таблица Менделеева" }),
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Закрыть таблицу Менделеева" }),
    );

    expect(
      screen.queryByRole("dialog", { name: "Таблица Менделеева" }),
    ).not.toBeInTheDocument();
  });

  it("closes via the header close button", async () => {
    render(<PeriodicTableOverlay />);

    await userEvent.click(
      screen.getByRole("button", { name: "Таблица Менделеева" }),
    );

    await userEvent.click(screen.getByRole("button", { name: "Закрыть" }));

    expect(
      screen.queryByRole("dialog", { name: "Таблица Менделеева" }),
    ).not.toBeInTheDocument();
  });
});
