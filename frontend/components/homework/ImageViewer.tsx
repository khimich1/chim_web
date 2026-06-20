"use client";

import {
  useCallback,
  useRef,
  useState,
  type PointerEvent,
  type WheelEvent,
} from "react";

import { AuthenticatedImage } from "@/components/common/AuthenticatedImage";

const MIN_SCALE = 0.5;
const MAX_SCALE = 4;

export function ImageViewer({
  src,
  alt,
}: {
  src: string;
  alt: string;
}) {
  const [scale, setScale] = useState(1);
  const [rotation, setRotation] = useState(0);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const dragging = useRef(false);
  const lastPos = useRef({ x: 0, y: 0 });

  const reset = useCallback(() => {
    setScale(1);
    setRotation(0);
    setOffset({ x: 0, y: 0 });
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
    event.currentTarget.setPointerCapture(event.pointerId);
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
    event.currentTarget.releasePointerCapture(event.pointerId);
  }, []);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={rotate}
          className="rounded-md border border-zinc-300 bg-white px-2 py-1 text-xs text-zinc-700 hover:border-zinc-400"
        >
          ↻ 90°
        </button>
        <button
          type="button"
          onClick={reset}
          className="rounded-md border border-zinc-300 bg-white px-2 py-1 text-xs text-zinc-700 hover:border-zinc-400"
        >
          Сброс
        </button>
      </div>
      <div
        className="relative h-64 cursor-grab overflow-hidden rounded-md border border-zinc-200 bg-zinc-50 active:cursor-grabbing md:h-80"
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        role="region"
        aria-label={alt}
      >
        <div
          className="absolute left-1/2 top-1/2 origin-center"
          style={{
            transform: `translate(calc(-50% + ${offset.x}px), calc(-50% + ${offset.y}px)) scale(${scale}) rotate(${rotation}deg)`,
          }}
        >
          <AuthenticatedImage
            src={src}
            alt={alt}
            className="max-h-72 max-w-full select-none object-contain md:max-h-96"
          />
        </div>
      </div>
    </div>
  );
}
