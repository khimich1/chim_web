export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Default client-side timeout so a dead backend does not block UI for ~5 minutes. */
export const API_FETCH_TIMEOUT_MS = 15_000;

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Map fetch/network failures to user-facing Russian messages. */
export function formatFetchError(err: unknown, fallback: string): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) {
    if (err.name === "AbortError" || err.name === "TimeoutError") {
      return "Не удалось связаться с API. Запустите backend на порту 8000.";
    }
    if (err.message === "Failed to fetch") {
      return "Не удалось связаться с API. Запустите backend на порту 8000.";
    }
    return err.message;
  }
  return fallback;
}

/**
 * Client-side fetch wrapper. Always sends cookies (`credentials: "include"`)
 * so the httpOnly auth cookie issued by FastAPI is attached to every request.
 */
export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    ...init,
    signal: init.signal ?? AbortSignal.timeout(API_FETCH_TIMEOUT_MS),
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = await response.json();
      if (typeof data?.detail === "string") {
        detail = data.detail;
      } else if (Array.isArray(data?.detail)) {
        detail = data.detail
          .map((item: { msg?: string; loc?: unknown[] }) => {
            const field = Array.isArray(item.loc)
              ? item.loc.filter((part) => part !== "body").join(".")
              : "";
            return field ? `${field}: ${item.msg ?? "ошибка"}` : (item.msg ?? "ошибка");
          })
          .join("; ");
      }
    } catch {
      // non-JSON error body — keep status text
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}
