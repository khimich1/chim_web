import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { LeadForm } from "@/components/marketing/LeadForm";
import { submitLead } from "@/lib/api/leads";

const searchParams = new URLSearchParams(
  "utm_source=vk&utm_medium=cpc&utm_campaign=aug2026_diag",
);

vi.mock("next/navigation", () => ({
  useSearchParams: () => searchParams,
}));

vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    ...rest
  }: {
    href: string;
    children: React.ReactNode;
  }) => (
    <a href={href} {...rest}>
      {children}
    </a>
  ),
}));

vi.mock("@/lib/api/leads", () => ({
  submitLead: vi.fn(),
}));

const mockedSubmitLead = vi.mocked(submitLead);

beforeEach(() => {
  vi.clearAllMocks();
});

async function fillRequiredFields() {
  await userEvent.type(screen.getByLabelText(/Имя родителя/), "Анна");
  await userEvent.type(screen.getByLabelText("Телефон"), "+79001234567");
}

describe("LeadForm", () => {
  it("disables submit until privacy checkbox is checked", async () => {
    render(<LeadForm sourcePage="/zapis" />);

    await fillRequiredFields();

    const button = screen.getByRole("button", { name: "Записаться на диагностику" });
    expect(button).toBeDisabled();

    await userEvent.click(screen.getByRole("checkbox"));
    expect(button).toBeEnabled();
  });

  it("submits with UTM params from searchParams", async () => {
    mockedSubmitLead.mockResolvedValue({ id: "1", status: "accepted" });

    render(<LeadForm sourcePage="/zapis" />);
    await fillRequiredFields();
    await userEvent.click(screen.getByRole("checkbox"));
    await userEvent.click(screen.getByRole("button", { name: "Записаться на диагностику" }));

    expect(mockedSubmitLead).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "Анна",
        phone: "+79001234567",
        source_page: "/zapis",
        utm_source: "vk",
        utm_medium: "cpc",
        utm_campaign: "aug2026_diag",
      }),
    );

    expect(
      await screen.findByText("Спасибо! Перезвоним в течение 2 часов"),
    ).toBeInTheDocument();
  });

  it("shows error message on submit failure", async () => {
    mockedSubmitLead.mockRejectedValue(new Error("submit_failed"));

    render(<LeadForm sourcePage="/zapis" />);
    await fillRequiredFields();
    await userEvent.click(screen.getByRole("checkbox"));
    await userEvent.click(screen.getByRole("button", { name: "Записаться на диагностику" }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Записаться на диагностику" })).toBeEnabled();
  });
});
