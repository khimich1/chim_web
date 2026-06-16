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
    <div>
      <div className="mb-1 flex items-center justify-between text-sm text-zinc-600">
        <span>
          Шаг {current} из {total}
        </span>
        <span>{percent}%</span>
      </div>
      <div
        className="h-2 w-full overflow-hidden rounded-full bg-zinc-200"
        role="progressbar"
        aria-valuenow={current}
        aria-valuemin={0}
        aria-valuemax={total}
      >
        <div
          className="h-full rounded-full bg-chem-royal transition-all"
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}
