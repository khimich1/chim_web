import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import { MessageBubble } from "@/components/tutor/MessageBubble";
import type { TutorMessage } from "@/lib/api/tutor";

function assistantMessage(content: string): TutorMessage {
  return {
    id: "a1",
    role: "assistant",
    content,
    created_at: "2026-06-18T10:00:00Z",
  };
}

function userMessage(content: string): TutorMessage {
  return {
    id: "u1",
    role: "user",
    content,
    created_at: "2026-06-18T10:00:00Z",
  };
}

describe("MessageBubble", () => {
  it("renders basic markdown for assistant messages", () => {
    render(
      <MessageBubble
        message={assistantMessage("**Алканы** — насыщенные углеводороды.\n\n- метан\n- этан")}
      />,
    );

    const strong = screen.getByText("Алканы");
    expect(strong.tagName).toBe("STRONG");
    expect(screen.getByText("метан")).toBeInTheDocument();
    expect(screen.getByText("этан")).toBeInTheDocument();
  });

  it("renders fenced code blocks for assistant messages", () => {
    render(
      <MessageBubble
        message={assistantMessage("Пример:\n\n```\nCH4 + Cl2\n```")}
      />,
    );

    expect(screen.getByText("CH4 + Cl2")).toBeInTheDocument();
    const code = screen.getByText("CH4 + Cl2");
    expect(code.closest("pre")).not.toBeNull();
  });

  it("strips script tags and does not execute XSS payloads", () => {
    const { container } = render(
      <MessageBubble
        message={assistantMessage(
          '<script>alert("xss")</script>**безопасно**',
        )}
      />,
    );

    expect(container.querySelector("script")).toBeNull();
    expect(screen.getByText("безопасно").tagName).toBe("STRONG");
    expect(screen.queryByText(/alert/)).not.toBeInTheDocument();
  });

  it("keeps user messages as plain pre-wrapped text", () => {
    render(<MessageBubble message={userMessage("**не жирный**")} />);

    expect(screen.getByText("**не жирный**")).toBeInTheDocument();
    expect(screen.queryByRole("strong")).not.toBeInTheDocument();
  });
});
