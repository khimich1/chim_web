/** Corner decorative blobs — low opacity, side corridors, calm lava-lamp CSS drift+morph. */
export function DecorativeBlobs({
  className = "",
  scoped = false,
}: {
  className?: string;
  /** When true, blobs fill a relative parent instead of the viewport. */
  scoped?: boolean;
}) {
  // Global must NOT use negative z-index: as a body child it would paint
  // behind body's own background (chem-surface). Layout wraps page content
  // in a higher stacking layer so blobs sit between bg and UI.
  const positionClass = scoped
    ? "absolute inset-0 z-0"
    : "fixed inset-0 z-0";

  return (
    <div
      className={`pointer-events-none overflow-hidden ${positionClass} ${className}`}
      aria-hidden="true"
    >
      {/* L corridor — top */}
      <svg
        className="chem-blob-drift chem-blob-drift--a absolute -left-20 -top-24 h-64 w-64 opacity-[0.18]"
        viewBox="0 0 200 200"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          fill="var(--blob-teal)"
          d="M45 18c28-8 58 6 72 32s4 58-18 74-54 18-72-2S17 46 45 18z"
        />
      </svg>
      {/* R corridor — mid */}
      <svg
        className="chem-blob-drift chem-blob-drift--c absolute -right-16 top-[22%] h-56 w-56 opacity-[0.14]"
        viewBox="0 0 200 200"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          fill="var(--blob-amber)"
          d="M120 30c36 4 64 34 66 70s-22 72-56 78-70-22-74-58 28-90 64-90z"
        />
      </svg>
      {/* L corridor — bottom */}
      <svg
        className="chem-blob-drift chem-blob-drift--b absolute -bottom-28 -left-14 h-72 w-72 opacity-[0.12]"
        viewBox="0 0 200 200"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          fill="var(--blob-slate)"
          d="M30 110c18-34 56-48 88-34s52 46 44 78-40 58-74 52S12 144 30 110z"
        />
      </svg>
      {/* R corridor — bottom */}
      <svg
        className="chem-blob-drift chem-blob-drift--d absolute -bottom-20 -right-20 h-60 w-60 opacity-[0.16]"
        viewBox="0 0 200 200"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          fill="var(--blob-peach)"
          d="M95 55c30-6 58 12 68 40s-2 60-28 74-62 8-76-22 6-86 36-92z"
        />
      </svg>
    </div>
  );
}
