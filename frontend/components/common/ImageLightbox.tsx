"use client";

import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type PointerEvent,
  type RefObject,
  type WheelEvent,
} from "react";

import { AuthenticatedImage } from "@/components/common/AuthenticatedImage";

const MIN_SCALE = 0.5;
const MAX_SCALE = 4;
const ZOOM_STEP = 0.25;

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

export type LightboxItem = { src: string; alt: string };

export function ImageLightbox({
  open,
  items,
  index,
  onClose,
  onIndexChange,
  triggerRef,
}: {
  open: boolean;
  items: LightboxItem[];
  index: number;
  onClose: () => void;
  onIndexChange?: (next: number) => void;
  /** Optional explicit trigger; otherwise focus returns to document.activeElement at open. */
  triggerRef?: RefObject<HTMLElement | null>;
}) {
  const titleId = useId();
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  const [scale, setScale] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const dragging = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });

  const resetTransform = useCallback(() => {
    setScale(1);
    setRotation(0);
    setOffset({ x: 0, y: 0 });
  }, []);

  useEffect(() => {
    if (!open) {
      return;
    }
    resetTransform();
  }, [open, index, resetTransform]);

  useEffect(() => {
    if (!open || items.length === 0) {
      return;
    }

    returnFocusRef.current =
      (triggerRef?.current as HTMLElement | null) ??
      (document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null);

    closeRef.current?.focus();

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
        return;
      }

      if (event.key === "Tab" && dialogRef.current) {
        const focusable = getFocusableElements(dialogRef.current);
        if (focusable.length === 0) {
          event.preventDefault();
          dialogRef.current.focus();
          return;
        }
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        const active = document.activeElement;

        if (event.shiftKey) {
          if (active === first || !dialogRef.current.contains(active)) {
            event.preventDefault();
            last.focus();
          }
        } else if (active === last || !dialogRef.current.contains(active)) {
          event.preventDefault();
          first.focus();
        }
        return;
      }

      if (items.length <= 1 || !onIndexChange) {
        return;
      }
      if (event.key === "ArrowRight") {
        event.preventDefault();
        if (index < items.length - 1) {
          onIndexChange(index + 1);
        }
      } else if (event.key === "ArrowLeft") {
        event.preventDefault();
        if (index > 0) {
          onIndexChange(index - 1);
        }
      }
    }

    document.addEventListener("keydown", onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
      returnFocusRef.current?.focus();
    };
  }, [open, items.length, index, onClose, onIndexChange, triggerRef]);

  const zoomIn = useCallback(() => {
    setScale((value) => Math.min(MAX_SCALE, value + ZOOM_STEP));
  }, []);

  const zoomOut = useCallback(() => {
    setScale((value) => Math.max(MIN_SCALE, value - ZOOM_STEP));
  }, []);

  const rotate = useCallback(() => {
    setRotation((value) => (value + 90) % 360);
  }, []);

  const onWheel = useCallback((event: WheelEvent<HTMLDivElement>) => {
    event.preventDefault();
    const delta = event.deltaY > 0 ? -0.1 : 0.1;
    setScale((value) => Math.min(MAX_SCALE, Math.max(MIN_SCALE, value + delta)));
  }, []);

  const onPointerDown = useCallback((event: PointerEvent<HTMLDivElement>) => {
    dragging.current = true;
    lastPos.current = { x: event.clientX, y: event.clientY };
    event.currentTarget.setPointerCapture?.(event.pointerId);
  }, []);

  const onPointerMove = useCallback((event: PointerEvent<HTMLDivElement>) => {
    if (!dragging.current) {
      return;
    }
    setOffset((current) => ({
      x: current.x + event.clientX - lastPos.current.x,
      y: current.y + event.clientY - lastPos.current.y,
    }));
    lastPos.current = { x: event.clientX, y: event.clientY };
  }, []);

  const onPointerUp = useCallback((event: PointerEvent<HTMLDivElement>) => {
    dragging.current = false;
    event.currentTarget.releasePointerCapture?.(event.pointerId);
  }, []);

  if (!open || items.length === 0) {
    return null;
  }

  const safeIndex = Math.min(Math.max(index, 0), items.length - 1);
  const current = items[safeIndex] ?? items[0];
  const showNav = items.length > 1;

  const toolbarBtnClass =
    "chem-btn-ghost px-2 py-1 text-xs text-zinc-800 disabled:cursor-not-allowed disabled:opacity-40";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4">
      <button
        type="button"
        className="absolute inset-0 bg-zinc-900/20"
        aria-label="Закрыть фон"
        tabIndex={-1}
        onClick={onClose}
      />

      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className="chem-card relative z-10 flex max-h-[min(96vh,920px)] w-full max-w-5xl flex-col overflow-hidden rounded-xl text-zinc-800 shadow-2xl"
      >
        <header className="flex items-center justify-between gap-3 border-b border-zinc-200 bg-chem-surface-muted/60 px-3 py-2 sm:px-4">
          <h2 id={titleId} className="truncate text-sm font-medium text-zinc-800">
            {current.alt}
            {showNav ? (
              <span className="ml-2 text-zinc-500" aria-live="polite">
                {safeIndex + 1} из {items.length}
              </span>
            ) : null}
          </h2>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            className="chem-btn-ghost min-h-[40px] min-w-[40px] px-3 py-1.5 text-sm text-zinc-800"
            aria-label="Закрыть"
          >
            ✕
          </button>
        </header>

        <div className="flex flex-wrap items-center gap-2 border-b border-zinc-200 bg-chem-card px-3 py-2 sm:px-4">
          <button
            type="button"
            onClick={zoomOut}
            className={toolbarBtnClass}
            aria-label="Уменьшить"
          >
            −
          </button>
          <button
            type="button"
            onClick={zoomIn}
            className={toolbarBtnClass}
            aria-label="Увеличить"
          >
            +
          </button>
          <button
            type="button"
            onClick={rotate}
            className={toolbarBtnClass}
          >
            ↻ 90°
          </button>
          <button
            type="button"
            onClick={resetTransform}
            className={toolbarBtnClass}
          >
            Сброс
          </button>
          {showNav ? (
            <>
              <button
                type="button"
                onClick={() => onIndexChange?.(safeIndex - 1)}
                disabled={safeIndex <= 0}
                className={toolbarBtnClass}
                aria-label="Предыдущее"
              >
                ←
              </button>
              <button
                type="button"
                onClick={() => onIndexChange?.(safeIndex + 1)}
                disabled={safeIndex >= items.length - 1}
                className={toolbarBtnClass}
                aria-label="Следующее"
              >
                →
              </button>
            </>
          ) : null}
        </div>

        <div className="relative flex min-h-0 flex-1 items-center justify-center bg-chem-bg/70 p-2 sm:p-4">
          <div
            className="relative h-[min(70vh,640px)] w-full cursor-grab overflow-hidden rounded-md border border-zinc-200/40 bg-white/30 active:cursor-grabbing"
            onWheel={onWheel}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerCancel={onPointerUp}
            role="region"
            aria-label={current.alt}
          >
            <div
              className="absolute left-1/2 top-1/2 origin-center"
              style={{
                transform: `translate(calc(-50% + ${offset.x}px), calc(-50% + ${offset.y}px)) scale(${scale}) rotate(${rotation}deg)`,
              }}
            >
              <AuthenticatedImage
                src={current.src}
                alt={current.alt}
                className="max-h-[min(68vh,600px)] max-w-[min(90vw,880px)] select-none object-contain"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
