import type { TestSession } from "@/lib/api/types";

export function formatSessionTitle(session: TestSession): string {
  if (session.variant_ref) {
    return `Вариант ${session.variant_ref.replace(/\.txt$/, "")}`;
  }
  if (session.homework_assignment_id) {
    return "Домашнее задание";
  }
  return "Смешанная сессия";
}
