export function ProgressBar({
  current,
  total,
}: {
  current: number;
  total: number;
}) {
  const safeTotal = Math.max(total, 1);
  const percent = Math.round((current / safeTotal) * 100);

  return (
    <div className="chem-progress-pill px-4 py-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-sm font-medium text-chem-teal-dark">
          Шаг {current} из {total}
        </span>
        <span className="chem-progress-pill__percent" aria-hidden="true">
          {percent}%
        </span>
      </div>
      <div
        className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-chem-teal-soft"
        role="progressbar"
        aria-valuenow={current}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-label={`Прогресс: ${percent}%, шаг ${current} из ${total}`}
      >
        <div
          className="h-full rounded-full bg-chem-teal transition-all duration-300"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
