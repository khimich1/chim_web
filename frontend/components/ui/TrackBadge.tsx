import type { Track } from "@/lib/api/types";

const LABELS: Record<Track, string> = {
  ege: "ЕГЭ",
  oge: "ОГЭ",
};

export function TrackBadge({ track }: { track: Track }) {
  return (
    <span className={track === "ege" ? "chem-badge-ege" : "chem-badge-oge"}>
      {LABELS[track]}
    </span>
  );
}
