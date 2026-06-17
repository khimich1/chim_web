/** Contour double-neck flask — brand mark (SPEC §14.2). */
export function BrandLogo({
  className = "",
  size = 32,
  label = "Химия",
}: {
  className?: string;
  size?: number;
  label?: string;
}) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
        className="shrink-0 text-chem-teal"
      >
        <path
          d="M10 4h4v3.5l-4.5 14.5A4 4 0 0 0 13.3 27h5.4a4 4 0 0 0 3.8-5L18 7.5V4h4"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M14 4h4M12 14h8"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeLinecap="round"
        />
        <ellipse
          cx="16"
          cy="22.5"
          rx="5.5"
          ry="2.25"
          stroke="currentColor"
          strokeWidth="1.5"
        />
      </svg>
      {label ? (
        <span className="text-sm font-semibold text-chem-teal-dark">{label}</span>
      ) : null}
    </span>
  );
}
