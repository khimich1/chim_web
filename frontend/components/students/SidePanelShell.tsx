"use client";

import {
  useCallback,
  useEffect,
  useId,
  useRef,
  type ReactNode,
  type RefObject,
} from "react";

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "button:not([disabled])",
  "textarea:not([disabled])",
  "input:not([disabled])",
  "select:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(", ");

function getFocusableElements(container: HTMLElement): HTMLElement[] {
  return Array.from(
    container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
  ).filter((el) => !el.hasAttribute("disabled") && el.tabIndex !== -1);
}

export function SidePanelShell({
  open,
  title,
  onClose,
  children,
  titleId: titleIdProp,
  returnFocusRef,
  initialFocusRef,
}: {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  titleId?: string;
  returnFocusRef?: RefObject<HTMLElement | null>;
  initialFocusRef?: RefObject<HTMLElement | null>;
}) {
  const generatedTitleId = useId();
  const titleId = titleIdProp ?? generatedTitleId;
  const panelRef = useRef<HTMLElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);

  const handleClose = useCallback(() => {
    onClose();
  }, [onClose]);

  useEffect(() => {
    if (!open) {
      return;
    }

    const returnTarget =
      (returnFocusRef?.current as HTMLElement | null) ??
      (document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null);

    const focusTarget =
      initialFocusRef?.current ?? closeRef.current ?? panelRef.current;
    focusTarget?.focus();

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        handleClose();
        return;
      }

      if (event.key !== "Tab" || !panelRef.current) {
        return;
      }

      const focusable = getFocusableElements(panelRef.current);
      if (focusable.length === 0) {
        event.preventDefault();
        panelRef.current.focus();
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement;

      if (event.shiftKey) {
        if (active === first || active === panelRef.current) {
          event.preventDefault();
          last.focus();
        }
      } else if (active === last) {
        event.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
      returnTarget?.focus();
    };
  }, [open, handleClose, returnFocusRef, initialFocusRef]);

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50">
      <button
        type="button"
        className="absolute inset-0 bg-black/40"
        aria-label="Закрыть панель"
        onClick={handleClose}
      />

      <aside
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className="absolute inset-y-0 right-0 z-10 flex w-full max-w-md flex-col border-l border-zinc-200 bg-white shadow-xl outline-none sm:max-w-lg"
      >
        <header className="flex items-center justify-between gap-3 border-b border-zinc-200 px-4 py-3">
          <h2
            id={titleId}
            className="text-base font-semibold text-zinc-900"
          >
            {title}
          </h2>
          <button
            ref={closeRef}
            type="button"
            onClick={handleClose}
            className="rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-800 hover:bg-zinc-100"
          >
            Закрыть
          </button>
        </header>
        <div className="flex-1 overflow-y-auto px-4 py-4">{children}</div>
      </aside>
    </div>
  );
}
