import { test, expect } from "@playwright/test";

const studentEmail = process.env.E2E_STUDENT_EMAIL ?? "e2e-student@example.com";
const studentPassword = process.env.E2E_STUDENT_PASSWORD ?? "e2e-student-pass";
const homeworkId = process.env.E2E_HOMEWORK_ID;
const correctAnswer = process.env.E2E_CORRECT_ANSWER ?? "1";

test.describe("Smoke E2E (Task 99)", () => {
  test("login → one test step → submit homework", async ({ page }) => {
    test.skip(!homeworkId, "Set E2E_HOMEWORK_ID (python -m app.cli.seed_e2e)");

    await page.goto("/login");
    await page.getByLabel("Email").fill(studentEmail);
    await page.getByLabel("Пароль").fill(studentPassword);
    await page.getByRole("button", { name: "Войти" }).click();

    await expect(page).toHaveURL(/\/student/, { timeout: 15_000 });

    const skipWelcome = page.getByRole("button", { name: "Позже, посмотрю сам" });
    if (await skipWelcome.isVisible().catch(() => false)) {
      await skipWelcome.click();
      await expect(page).toHaveURL(/\/student$/);
    }

    await page.goto(`/student/homework/${homeworkId}`);
    await page.getByRole("button", { name: "Начать тест" }).click();

    await expect(page).toHaveURL(/\/student\/tests\/sessions\//, {
      timeout: 15_000,
    });

    await page.getByLabel("Ваш ответ").fill(correctAnswer);
    await page.getByRole("button", { name: "Проверить" }).click();
    await expect(page.getByRole("status").filter({ hasText: "Верно" })).toBeVisible({
      timeout: 15_000,
    });

    await page.getByRole("button", { name: "Завершить" }).click();
    await expect(page).toHaveURL(/\/summary$/, { timeout: 15_000 });

    await page.getByRole("button", { name: "Сдать домашнее задание" }).click();
    await expect(page.getByText(/сдано/i)).toBeVisible({ timeout: 15_000 });
  });
});
