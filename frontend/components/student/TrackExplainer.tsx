import type { Track } from "@/lib/api/types";
import { TrackBadge } from "@/components/ui/TrackBadge";

const TRACK_COPY: Record<
  Track,
  { title: string; body: string }
> = {
  ege: {
    title: "ЕГЭ по химии",
    body: "Тесты, задания и лекции подготовлены под формат единого государственного экзамена (11 класс).",
  },
  oge: {
    title: "ОГЭ по химии",
    body: "Материалы и тесты соответствуют основному государственному экзамену (9 класс).",
  },
};

export function TrackExplainer({ track }: { track: Track }) {
  const copy = TRACK_COPY[track];

  return (
    <div className="rounded-lg border border-chem-teal/20 bg-chem-teal/5 px-4 py-3">
      <div className="flex flex-wrap items-center gap-2">
        <TrackBadge track={track} />
        <span className="text-sm font-medium text-zinc-800">{copy.title}</span>
      </div>
      <p className="mt-2 text-sm text-zinc-600">{copy.body}</p>
    </div>
  );
}
