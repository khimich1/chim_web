"use client";

import { useId, useState } from "react";

import { SolubilityTableContent } from "@/components/tests/SolubilityTableContent";
import { useReferenceDialog } from "@/components/tests/useReferenceDialog";

export function SolubilityTableOverlay() {
  const [open, setOpen] = useState(false);
  const titleId = useId();
  const { triggerRef, closeRef, handleClose } = useReferenceDialog(open, () =>
    setOpen(false),
  );

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setOpen(true)}
        className="min-h-[44px] w-full rounded-full border border-chem-teal/30 bg-white px-4 py-3 text-sm font-medium text-chem-teal shadow-lg transition hover:bg-chem-teal-soft sm:w-auto"
        aria-expanded={open}
        aria-haspopup="dialog"
        aria-controls={open ? titleId : undefined}
      >
        Таблица растворимости
      </button>

      {open ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4">
          <button
            type="button"
            className="absolute inset-0 bg-black/60"
            aria-label="Закрыть таблицу растворимости"
            onClick={handleClose}
          />

          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            className="relative z-10 flex max-h-[min(94vh,920px)] w-full max-w-6xl flex-col overflow-hidden rounded-xl border border-zinc-200 bg-chem-bg shadow-2xl"
          >
            <header className="flex items-center justify-between gap-3 border-b border-chem-teal-soft bg-chem-teal px-4 py-3 text-white">
              <h2 id={titleId} className="text-sm font-semibold sm:text-base">
                Таблица растворимости
              </h2>
              <button
                ref={closeRef}
                type="button"
                onClick={handleClose}
                className="chem-btn-ghost min-h-[44px] min-w-[44px] shrink-0 border-white/30 bg-white/10 px-3 py-2 text-sm text-white hover:bg-white/20"
                aria-label="Закрыть"
              >
                ✕
              </button>
            </header>

            <div className="overflow-auto bg-chem-card">
              <SolubilityTableContent />
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
