"use client";

export const CAPTURE_CHECKLIST_ITEMS = [
  "Весь лист в кадре",
  "Хорошее освещение",
  "Без размытия",
] as const;

interface CaptureChecklistProps {
  checked: boolean[];
  onToggle: (index: number) => void;
  disabled?: boolean;
}

export function CaptureChecklist({
  checked,
  onToggle,
  disabled = false,
}: CaptureChecklistProps) {
  return (
    <ul className="flex flex-col gap-3" aria-label="Чеклист перед съёмкой">
      {CAPTURE_CHECKLIST_ITEMS.map((label, index) => (
        <li key={label}>
          <label className="flex min-h-[44px] cursor-pointer items-center gap-3 text-sm text-zinc-800">
            <input
              type="checkbox"
              className="h-5 w-5 rounded border-zinc-300"
              checked={checked[index] ?? false}
              disabled={disabled}
              onChange={() => onToggle(index)}
            />
            <span>{label}</span>
          </label>
        </li>
      ))}
    </ul>
  );
}

export function isCaptureChecklistComplete(checked: boolean[]): boolean {
  return CAPTURE_CHECKLIST_ITEMS.every((_, index) => checked[index] === true);
}
