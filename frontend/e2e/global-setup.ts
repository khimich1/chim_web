import type { FullConfig } from "@playwright/test";

const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:8080";
const healthUrl = `${baseURL.replace(/\/$/, "")}/health`;

async function waitForHealth(timeoutMs = 120_000): Promise<void> {
  const started = Date.now();
  let lastError: unknown;

  while (Date.now() - started < timeoutMs) {
    try {
      const response = await fetch(healthUrl, { signal: AbortSignal.timeout(5_000) });
      if (response.ok) {
        return;
      }
      lastError = new Error(`Health check returned ${response.status}`);
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 2_000));
  }

  throw new Error(
    `Backend not ready at ${healthUrl} after ${timeoutMs}ms: ${String(lastError)}`,
  );
}

export default async function globalSetup(_config: FullConfig): Promise<void> {
  await waitForHealth();

  if (!process.env.E2E_HOMEWORK_ID) {
    console.warn(
      "[e2e] E2E_HOMEWORK_ID is not set. Run: cd backend && python -m app.cli.seed_e2e",
    );
  }
  if (!process.env.E2E_WRITTEN_HOMEWORK_ID) {
    console.warn(
      "[e2e] E2E_WRITTEN_HOMEWORK_ID is not set. seed_e2e JSON field: writtenHomeworkId",
    );
  }
}
