import type { HomeworkItem, HomeworkItemKind, Track } from "@/lib/api/types";

export function formatHomeworkItemLabel(item: HomeworkItem): string {
  if (item.kind === "lecture") {
    return `Лекция: ${item.topic}`;
  }
  if (item.kind === "test_variant") {
    return `Тест: вариант ${item.variant.replace(/\.txt$/, "")}`;
  }
  if (item.kind === "test_by_type") {
    const numbers = item.types.join(", ");
    return `Тест: №${numbers} по всем вариантам`;
  }
  return `Тест: ${item.variant.replace(/\.txt$/, "")}, задания ${item.types.join(", ")}`;
}

export function isTestHomeworkItem(
  item: HomeworkItem,
): item is Extract<
  HomeworkItem,
  { kind: "test_variant" | "test_partial" | "test_by_type" }
> {
  return (
    item.kind === "test_variant" ||
    item.kind === "test_partial" ||
    item.kind === "test_by_type"
  );
}

export function typeNumbersForTrack(track: Track): number[] {
  const max = track === "ege" ? 28 : 19;
  return Array.from({ length: max }, (_, index) => index + 1);
}

/** Rough step count hint for test_by_type (EGE ≈30 per type, OGE ≈30 per type). */
export function estimateTestByTypeSteps(
  types: number[],
  track: Track,
): number {
  const perType = track === "ege" ? 30 : 30;
  return types.length * perType;
}

export function homeworkItemsSummary(items: HomeworkItem[]): string {
  if (items.length === 0) {
    return "Нет пунктов";
  }
  if (items.length === 1) {
    return formatHomeworkItemLabel(items[0]);
  }
  const kinds: Record<HomeworkItemKind, number> = {
    lecture: 0,
    test_variant: 0,
    test_partial: 0,
    test_by_type: 0,
  };
  for (const item of items) {
    kinds[item.kind] += 1;
  }
  const parts: string[] = [];
  if (kinds.lecture > 0) {
    parts.push(`${kinds.lecture} лекц.`);
  }
  const testCount =
    kinds.test_variant + kinds.test_partial + kinds.test_by_type;
  if (testCount > 0) {
    parts.push(`${testCount} тест.`);
  }
  return `${items.length} пункта: ${parts.join(", ")}`;
}
