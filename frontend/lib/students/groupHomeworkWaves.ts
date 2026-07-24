import type { HomeworkAssignment, HomeworkStatus } from "@/lib/api/types";

export interface GroupHomeworkWave {
  assignBatchId: string;
  anchorId: string;
  title: string;
  dueAt: string | null;
  createdAt: string;
  total: number;
  activeCount: number;
  submittedCount: number;
  cancelledCount: number;
  /** True when every copy is cancelled (no trash). */
  allCancelled: boolean;
  /** True when at least one copy is still assigned/in_progress. */
  canCancel: boolean;
}

const ACTIVE: ReadonlySet<HomeworkStatus> = new Set([
  "assigned",
  "in_progress",
]);
const SUBMITTED: ReadonlySet<HomeworkStatus> = new Set([
  "submitted",
  "reviewed",
]);

export function groupHomeworkWaves(
  rows: HomeworkAssignment[],
  groupId: string,
): GroupHomeworkWave[] {
  const byBatch = new Map<string, HomeworkAssignment[]>();
  for (const row of rows) {
    if (row.source_group_id !== groupId || !row.assign_batch_id) {
      continue;
    }
    const list = byBatch.get(row.assign_batch_id) ?? [];
    list.push(row);
    byBatch.set(row.assign_batch_id, list);
  }

  const waves: GroupHomeworkWave[] = [];
  for (const [assignBatchId, members] of byBatch) {
    const sorted = [...members].sort(
      (a, b) =>
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    );
    const activeCount = sorted.filter((row) => ACTIVE.has(row.status)).length;
    const submittedCount = sorted.filter((row) =>
      SUBMITTED.has(row.status),
    ).length;
    const cancelledCount = sorted.filter(
      (row) => row.status === "cancelled",
    ).length;
    const first = sorted[0];
    waves.push({
      assignBatchId,
      anchorId: first.id,
      title: first.title,
      dueAt: first.due_at,
      createdAt: first.created_at,
      total: sorted.length,
      activeCount,
      submittedCount,
      cancelledCount,
      allCancelled: cancelledCount === sorted.length,
      canCancel: activeCount > 0,
    });
  }

  return waves.sort(
    (a, b) =>
      new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
  );
}

export function formatWaveSummary(wave: GroupHomeworkWave): string {
  const parts = [`${wave.total} уч.`];
  if (wave.submittedCount > 0) {
    parts.push(`${wave.submittedCount} сдано`);
  }
  if (wave.activeCount > 0) {
    parts.push(`${wave.activeCount} активно`);
  }
  if (wave.cancelledCount > 0) {
    parts.push(
      wave.allCancelled
        ? "Отозвано"
        : `${wave.cancelledCount} отозвано`,
    );
  }
  return parts.join(" · ");
}
