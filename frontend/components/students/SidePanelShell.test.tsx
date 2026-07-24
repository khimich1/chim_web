import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { SidePanelShell } from "@/components/students/SidePanelShell";

describe("SidePanelShell", () => {
  it("renders dialog when open and closes on Escape", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <SidePanelShell open title="Карточка" onClose={onClose}>
        <p>Содержимое</p>
      </SidePanelShell>,
    );

    expect(screen.getByRole("dialog", { name: "Карточка" })).toBeInTheDocument();
    expect(screen.getByText("Содержимое")).toBeInTheDocument();

    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalled();
  });

  it("closes on backdrop click", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();

    render(
      <SidePanelShell open title="Карточка" onClose={onClose}>
        <p>Содержимое</p>
      </SidePanelShell>,
    );

    await user.click(screen.getByRole("button", { name: "Закрыть панель" }));
    expect(onClose).toHaveBeenCalled();
  });

  it("renders nothing when closed", () => {
    render(
      <SidePanelShell open={false} title="Карточка" onClose={() => undefined}>
        <p>Содержимое</p>
      </SidePanelShell>,
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});
