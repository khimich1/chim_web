"use client";

import { useState } from "react";

import { CreateStudentForm } from "@/components/students/CreateStudentForm";
import { GroupsPanel } from "@/components/students/GroupsPanel";
import { StudentList } from "@/components/students/StudentList";
import type {
  HomeworkTemplate,
  Student,
  TeacherStudentStats,
} from "@/lib/api/types";

export type StudentsHubTab = "add" | "list" | "groups";

const TABS: { id: StudentsHubTab; label: string }[] = [
  { id: "add", label: "Добавить" },
  { id: "list", label: "Ученики" },
  { id: "groups", label: "Группы" },
];

export function StudentsHub({
  students,
  stats = [],
  templates = [],
  initialTab = "list",
}: {
  students: Student[];
  stats?: TeacherStudentStats[];
  templates?: HomeworkTemplate[];
  initialTab?: StudentsHubTab;
}) {
  const [tab, setTab] = useState<StudentsHubTab>(initialTab);

  return (
    <div className="mt-10 flex flex-col gap-6">
      <div
        role="tablist"
        aria-label="Разделы учеников"
        className="inline-flex w-full rounded-lg border border-zinc-200 bg-zinc-50 p-1 sm:w-auto"
      >
        {TABS.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            id={`students-tab-${item.id}`}
            aria-selected={tab === item.id}
            aria-controls={`students-panel-${item.id}`}
            onClick={() => setTab(item.id)}
            className={`min-h-[44px] flex-1 rounded-md px-4 py-2 text-sm font-medium transition sm:flex-none ${
              tab === item.id
                ? "bg-white text-zinc-900 shadow-sm"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {tab === "add" ? (
        <section
          role="tabpanel"
          id="students-panel-add"
          aria-labelledby="students-tab-add"
        >
          <CreateStudentForm />
        </section>
      ) : null}

      {tab === "list" ? (
        <section
          role="tabpanel"
          id="students-panel-list"
          aria-labelledby="students-tab-list"
        >
          <h2 className="mb-4 text-lg font-semibold text-zinc-900">
            Список ({students.length})
          </h2>
          <StudentList students={students} stats={stats} templates={templates} />
        </section>
      ) : null}

      {tab === "groups" ? (
        <section
          role="tabpanel"
          id="students-panel-groups"
          aria-labelledby="students-tab-groups"
        >
          <GroupsPanel students={students} templates={templates} />
        </section>
      ) : null}
    </div>
  );
}
