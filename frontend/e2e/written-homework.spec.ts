import path from "node:path";

import { test, expect } from "@playwright/test";

import { loginAs, logout, skipStudentWelcomeIfShown } from "./helpers/auth";

const studentEmail = process.env.E2E_STUDENT_EMAIL ?? "e2e-student@example.com";
const studentPassword = process.env.E2E_STUDENT_PASSWORD ?? "e2e-student-pass";
const teacherEmail = process.env.E2E_TEACHER_EMAIL ?? "e2e-teacher@example.com";
const teacherPassword = process.env.E2E_TEACHER_PASSWORD ?? "e2e-teacher-pass";
const writtenHomeworkId = process.env.E2E_WRITTEN_HOMEWORK_ID;

const samplePhotoPath = path.resolve(
  process.cwd(),
  "..",
  "e2e-fixtures",
  "sample-answer.png",
);

const teacherFeedbackText =
  "E2E: хорошая работа, обратите внимание на оформление";

test.describe("Written homework E2E (Task 99 / §1.9.9)", () => {
  test("photo upload → submit → teacher text feedback → student badge", async ({
    page,
  }) => {
    test.skip(
      !writtenHomeworkId,
      "Set E2E_WRITTEN_HOMEWORK_ID (python -m app.cli.seed_e2e → writtenHomeworkId)",
    );

    await loginAs(page, studentEmail, studentPassword, /\/student/);
    await skipStudentWelcomeIfShown(page);

    await page.goto(`/student/homework/${writtenHomeworkId}`);
    await page.getByRole("button", { name: "Начать тест" }).click();
    await expect(page).toHaveURL(/\/student\/tests\/sessions\//, {
      timeout: 15_000,
    });

    await page.getByLabel("Ваш ответ").fill("мой письменный ответ");
    await page
      .locator('label:has-text("Прикрепить с этого устройства") input[type="file"]')
      .setInputFiles(samplePhotoPath);
    await expect(page.getByText("Фото прикреплено")).toBeVisible({
      timeout: 15_000,
    });

    await page.getByRole("button", { name: "Сравнить ответ" }).click();
    await expect(
      page.getByRole("status").filter({ hasText: "Ответ сохранён" }),
    ).toBeVisible({ timeout: 15_000 });

    await page.getByRole("button", { name: "Завершить" }).click();
    await expect(page).toHaveURL(/\/summary$/, { timeout: 15_000 });

    await page.getByRole("button", { name: "Сдать домашнее задание" }).click();
    await expect(page.getByText(/сдано/i)).toBeVisible({ timeout: 15_000 });

    await logout(page);

    await loginAs(page, teacherEmail, teacherPassword, /\/teacher/);
    await page.goto(`/teacher/homework/${writtenHomeworkId}`);
    await expect(page.getByText("Проверка письменных ответов")).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByText("Ответ ученика")).toBeVisible();

    const stepFeedbackForm = page
      .locator("li")
      .filter({ hasText: "Ответ ученика" })
      .first();
    await stepFeedbackForm.getByLabel("Текстовый комментарий").fill(teacherFeedbackText);
    await stepFeedbackForm.getByRole("button", { name: "Сохранить разбор" }).click();
    await expect(
      stepFeedbackForm.getByRole("status").filter({ hasText: "Разбор сохранён" }),
    ).toBeVisible({ timeout: 15_000 });

    await logout(page);

    await loginAs(page, studentEmail, studentPassword, /\/student/);
    await skipStudentWelcomeIfShown(page);

    await page.goto("/student/homework");
    const homeworkCard = page.locator("li").filter({ hasText: "E2E written" }).first();
    await expect(homeworkCard.getByText("Есть разбор")).toBeVisible({
      timeout: 15_000,
    });

    await page.goto(`/student/homework/${writtenHomeworkId}`);
    await expect(page.getByRole("heading", { name: "Разбор преподавателя" })).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByText(teacherFeedbackText)).toBeVisible();
  });
});
