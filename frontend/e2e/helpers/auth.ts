import { expect, type Page } from "@playwright/test";

export async function loginAs(
  page: Page,
  email: string,
  password: string,
  expectedUrl: RegExp,
): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Пароль").fill(password);
  await page.getByRole("button", { name: "Войти" }).click();
  await expect(page).toHaveURL(expectedUrl, { timeout: 15_000 });
}

export async function skipStudentWelcomeIfShown(page: Page): Promise<void> {
  const skipWelcome = page.getByRole("button", { name: "Позже, посмотрю сам" });
  if (await skipWelcome.isVisible().catch(() => false)) {
    await skipWelcome.click();
    await expect(page).toHaveURL(/\/student$/);
  }
}

export async function logout(page: Page): Promise<void> {
  await page.getByRole("button", { name: "Выйти" }).click();
  await expect(page).toHaveURL(/\/login/, { timeout: 15_000 });
}
