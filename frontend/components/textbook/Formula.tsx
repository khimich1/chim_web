import type { ReactNode } from "react";

/** Inline chemistry formula chip (SPEC §14.2 — backtick markdown → mono chip). */
export function Formula({ children }: { children: ReactNode }) {
  return <code className="chem-formula">{children}</code>;
}
