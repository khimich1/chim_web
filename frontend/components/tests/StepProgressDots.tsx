import type { TestStep } from "@/lib/api/types";

function dotClassName(step: TestStep, isCurrent: boolean): string {
  const classes = ["chem-step-dot"];

  if (step.status === "unseen") {
    classes.push("chem-step-dot--unseen");
  } else if (step.status === "answered") {
    classes.push("chem-step-dot--answered");
  } else if (step.is_correct) {
    classes.push("chem-step-dot--correct");
  } else {
    classes.push("chem-step-dot--incorrect");
  }

  if (isCurrent) {
    classes.push("chem-step-dot--current");
  }

  return classes.join(" ");
}

function stepAriaLabel(step: TestStep, stepNumber: number): string {
  if (step.status === "checked") {
    return step.is_correct
      ? `Задание ${stepNumber}: верно`
      : `Задание ${stepNumber}: неверно`;
  }
  if (step.status === "answered") {
    return `Задание ${stepNumber}: не проверено`;
  }
  return `Задание ${stepNumber}: не открыто`;
}

export function StepProgressDots({
  steps,
  current,
  onSelect,
}: {
  steps: TestStep[];
  current: number;
  onSelect: (index: number) => void;
}) {
  const scrollable = steps.length >= 15;

  return (
    <div className="chem-progress-pill px-4 py-3">
      <p className="text-sm font-medium text-chem-teal-dark">
        Шаг {current + 1} из {steps.length}
      </p>
      <div
        role="tablist"
        aria-label="Прогресс по заданиям"
        className={
          scrollable
            ? "chem-step-dots chem-step-dots--scroll mt-3"
            : "chem-step-dots mt-3"
        }
      >
        {steps.map((step, index) => {
          const isCurrent = index === current;

          return (
            <button
              key={step.position}
              type="button"
              role="tab"
              aria-current={isCurrent ? "step" : undefined}
              aria-label={stepAriaLabel(step, index + 1)}
              onClick={() => onSelect(index)}
              className={dotClassName(step, isCurrent)}
            >
              <span className="sr-only">{index + 1}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
