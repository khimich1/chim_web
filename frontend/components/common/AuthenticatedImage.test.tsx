import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

import { AuthenticatedImage } from "@/components/common/AuthenticatedImage";
import { fetchAuthenticatedImageBlob } from "@/lib/api/authenticated-image";

vi.mock("@/lib/api/authenticated-image", () => ({
  fetchAuthenticatedImageBlob: vi.fn(),
}));

const mockedFetch = vi.mocked(fetchAuthenticatedImageBlob);

describe("AuthenticatedImage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(globalThis.URL, "createObjectURL", {
      configurable: true,
      writable: true,
      value: vi.fn(() => "blob:image-test"),
    });
    Object.defineProperty(globalThis.URL, "revokeObjectURL", {
      configurable: true,
      writable: true,
      value: vi.fn(),
    });
  });

  it("shows loading then renders blob URL", async () => {
    mockedFetch.mockResolvedValue(new Blob(["png"], { type: "image/png" }));

    render(
      <AuthenticatedImage
        src="/api/uploads/images/abc-123"
        alt="Test image"
        className="test-class"
      />,
    );

    expect(screen.getByText("Загрузка…")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByRole("img", { name: "Test image" })).toHaveAttribute(
        "src",
        "blob:image-test",
      );
    });

    expect(mockedFetch).toHaveBeenCalledWith("/api/uploads/images/abc-123");
  });

  it("shows error message when fetch fails", async () => {
    mockedFetch.mockRejectedValue(new Error("network"));

    render(
      <AuthenticatedImage
        src="/api/uploads/images/missing"
        alt="Missing"
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Не удалось загрузить изображение")).toBeInTheDocument();
    });
  });
});
