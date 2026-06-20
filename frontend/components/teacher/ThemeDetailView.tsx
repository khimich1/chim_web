"use client";

import { useState } from "react";

import { TaskEditor } from "@/components/teacher/TaskEditor";
import { ThemeEditor } from "@/components/teacher/ThemeEditor";
import type { CustomTask, TeacherTheme } from "@/lib/api/types";

export function ThemeDetailView({
  initialTheme,
  initialTasks,
}: {
  initialTheme: TeacherTheme;
  initialTasks: CustomTask[];
}) {
  const [theme, setTheme] = useState(initialTheme);
  const [tasks, setTasks] = useState(initialTasks);
  const [editingTaskId, setEditingTaskId] = useState<string | "new" | null>(
    null,
  );

  function handleTaskSaved(task: CustomTask) {
    if (!task.id) {
      setTasks((current) => current.filter((item) => item.id !== ""));
      setEditingTaskId(null);
      return;
    }

    setTasks((current) => {
      const exists = current.some((item) => item.id === task.id);
      if (exists) {
        return current.map((item) => (item.id === task.id ? task : item));
      }
      return [...current, task].sort((a, b) => a.sort_order - b.sort_order);
    });
    setEditingTaskId(null);
  }

  return (
    <div className="flex flex-col gap-8">
      <ThemeEditor theme={theme} onSaved={setTheme} />

      <section className="flex flex-col gap-4">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-zinc-900">
            Задания ({tasks.length})
          </h2>
          {editingTaskId === null ? (
            <button
              type="button"
              onClick={() => setEditingTaskId("new")}
              className="chem-btn-primary px-4 py-2 text-sm"
            >
              Добавить задание
            </button>
          ) : null}
        </div>

        {editingTaskId === "new" ? (
          <TaskEditor
            themeId={theme.id}
            onSaved={handleTaskSaved}
            onCancel={() => setEditingTaskId(null)}
          />
        ) : null}

        {editingTaskId && editingTaskId !== "new" ? (
          <TaskEditor
            themeId={theme.id}
            task={tasks.find((task) => task.id === editingTaskId)}
            onSaved={handleTaskSaved}
            onCancel={() => setEditingTaskId(null)}
          />
        ) : null}

        <ul className="chem-card divide-y divide-zinc-200 overflow-hidden rounded-xl">
          {tasks.length === 0 ? (
            <li className="px-4 py-6 text-sm text-zinc-500 sm:px-5">
              Заданий пока нет. Добавьте первое задание.
            </li>
          ) : (
            tasks.map((task, index) => (
              <li
                key={task.id}
                className="flex items-center justify-between gap-3 px-4 py-3.5 sm:px-5"
              >
                <div className="min-w-0">
                  <p className="font-medium text-zinc-900">
                    {task.title?.trim() || `Задание ${index + 1}`}
                  </p>
                  <p className="text-xs text-zinc-500">
                    {task.grading_mode === "auto"
                      ? "Автопроверка"
                      : "Самопроверка"}
                    {" · "}
                    {task.question_blocks.length} блок(ов)
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setEditingTaskId(task.id)}
                  disabled={editingTaskId !== null}
                  className="rounded-md border border-zinc-300 px-3 py-1.5 text-sm text-zinc-700 hover:border-zinc-400 disabled:opacity-50"
                >
                  Изменить
                </button>
              </li>
            ))
          )}
        </ul>
      </section>
    </div>
  );
}
