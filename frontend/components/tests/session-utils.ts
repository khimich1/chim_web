import type { TestSession, TestStep } from "@/lib/api/types";
import {
  isCustomSelfCheck,
  isExamContentSelfCheck,
} from "@/lib/tests/grading-utils";

export function formatSessionTitle(session: TestSession): string {
  if (session.custom_theme_id || session.source === "custom") {
    return "Авторская тема";
  }
  if (session.variant_ref) {
    return `Вариант ${session.variant_ref.replace(/\.txt$/, "")}`;
  }
  if (session.homework_assignment_id) {
    return "Домашнее задание";
  }
  return "Смешанная сессия";
}

function stepLabel(step: TestStep, index: number): string {
  if (step.custom_task_id || step.question_blocks?.length) {
    return `Задание ${index + 1}`;
  }
  return `Задание ${step.type ?? index + 1}`;
}

function stepVerdict(step: TestStep): string {
  if (isExamContentSelfCheck(step)) {
    return step.status === "checked" ? "✓ Засчитано" : "— Не отвечено";
  }
  if (isCustomSelfCheck(step)) {
    return step.status === "checked" ? "Самопроверка" : "— Не отвечено";
  }
  if (step.is_correct === true) {
    return "✓ Верно";
  }
  if (step.is_correct === false) {
    return "✗ Неверно";
  }
  return "— Не отвечено";
}

function verdictClass(step: TestStep): string {
  if (isExamContentSelfCheck(step)) {
    return step.status === "checked"
      ? "chem-verdict-correct"
      : "bg-zinc-100 text-zinc-500";
  }
  if (isCustomSelfCheck(step)) {
    return step.status === "checked"
      ? "bg-chem-teal-soft text-chem-teal-dark"
      : "bg-zinc-100 text-zinc-500";
  }
  if (step.is_correct === true) {
    return "chem-verdict-correct";
  }
  if (step.is_correct === false) {
    return "chem-verdict-incorrect";
  }
  return "bg-zinc-100 text-zinc-500";
}

export { stepLabel, stepVerdict, verdictClass };
