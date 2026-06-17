import type { ReactNode } from "react";

import type { CalloutVariant } from "@/lib/textbook/markdown";

const CALLOUT_LABELS: Record<CalloutVariant, string> = {
  example: "Пример",
  important: "Важно",
  remember: "Запомни",
};

const CALLOUT_CLASSES: Record<CalloutVariant, string> = {
  example: "chem-callout chem-callout-example",
  important: "chem-callout chem-callout-important",
  remember: "chem-callout chem-callout-remember",
};

export function Callout({
  variant,
  children,
}: {
  variant: CalloutVariant;
  children: ReactNode;
}) {
  const label = CALLOUT_LABELS[variant];

  return (
    <aside
      className={CALLOUT_CLASSES[variant]}
      role="note"
      aria-label={label}
    >
      <p className="mb-1 text-sm font-semibold">{label}</p>
      <div className="chem-lecture-prose">{children}</div>
    </aside>
  );
}
