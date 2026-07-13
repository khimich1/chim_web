import Link from "next/link";

import type { TextbookSection } from "@/lib/api/types";

export function SectionPills({
  sections,
  activeSection,
}: {
  sections: TextbookSection[];
  activeSection: string;
}) {
  if (sections.length === 0) {
    return null;
  }

  return (
    <div
      role="group"
      aria-label="Разделы учебника"
      className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1"
    >
      {sections.map((section) => {
        const active = section.section_id === activeSection;
        return (
          <Link
            key={section.section_id}
            href={`/student/textbook?section=${encodeURIComponent(section.section_id)}`}
            aria-current={active ? "page" : undefined}
            className={`shrink-0 rounded-full px-4 py-2 text-sm font-medium transition ${
              active
                ? "bg-chem-teal text-white shadow-sm"
                : "border border-chem-teal/30 bg-white text-chem-teal hover:bg-chem-teal-soft/50"
            }`}
          >
            {section.title}
            <span className="ml-1.5 text-xs opacity-80">({section.topic_count})</span>
          </Link>
        );
      })}
    </div>
  );
}
