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

function getErrorName(err: unknown): string | undefined {
  if (typeof err === "object" && err !== null && "name" in err) {
    return String((err as { name: unknown }).name);
  }
  return undefined;
}

function apiUnreachableMessage(): string {
  return `Бэкенд не отвечает на ${API_URL}. Запустите: cd backend && uvicorn app.main:app --port 8000`;
}

function apiTimeoutMessage(): string {
  const seconds = API_FETCH_TIMEOUT_MS / 1000;
  return `Превышено время ожидания API (${seconds} с). Убедитесь, что backend запущен на ${API_URL}.`;
}

/** Map fetch/network failures to user-facing Russian messages. */
export function formatFetchError(err: unknown, fallback: string): string {
  if (err instanceof ApiError) return err.message;

  const errorName = getErrorName(err);
  if (errorName === "TimeoutError" || errorName === "AbortError") {
    return apiTimeoutMessage();
  }

  if (err instanceof Error) {
    if (err.message === "Failed to fetch") {
      return apiUnreachableMessage();
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
  const { signal: initSignal, ...restInit } = init;
  const useTimeout = process.env.VITEST !== "true" && initSignal === undefined;

  const response = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    ...restInit,
    ...(useTimeout
      ? { signal: AbortSignal.timeout(API_FETCH_TIMEOUT_MS) }
      : initSignal
        ? { signal: initSignal }
        : {}),
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
