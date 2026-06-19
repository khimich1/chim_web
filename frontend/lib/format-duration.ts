/** Format a minute count for dashboard stats (e.g. 90 → "1 ч 30 мин"). */
export function formatTotalMinutes(minutes: number): string {
  if (minutes < 60) {
    return `${minutes} мин`;
  }
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  return remainder > 0 ? `${hours} ч ${remainder} мин` : `${hours} ч`;
}

/** Elapsed time since an ISO timestamp (e.g. in-progress session). */
export function formatElapsedSince(
  createdAt: string,
  now: Date = new Date(),
): string {
  const start = new Date(createdAt);
  const diffMs = Math.max(0, now.getTime() - start.getTime());
  const minutes = Math.floor(diffMs / 60_000);

  if (minutes < 1) {
    return "меньше минуты";
  }
  if (minutes < 60) {
    return `${minutes} мин`;
  }

  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  if (remainder === 0) {
    return `${hours} ч`;
  }
  return `${hours} ч ${remainder} мин`;
}
