"use client";

import { Fragment, useState } from "react";
import { useRouter } from "next/navigation";

import { TrackBadge } from "@/components/ui/TrackBadge";
import { ApiError } from "@/lib/api/client";
import {
  deleteStudent,
  resetStudentPassword,
} from "@/lib/api/students";
import { assignHomeworkTemplate } from "@/lib/api/templates";
import { formatTotalMinutes } from "@/lib/format-duration";
import type {
  HomeworkTemplate,
  Student,
  TeacherStudentStats,
} from "@/lib/api/types";

function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
  }).format(new Date(iso));
}

function formatActiveDate(iso: string | null): string {
  if (!iso) {
    return "—";
  }
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
  }).format(new Date(iso));
}

export function StudentList({
  students,
  stats = [],
  templates = [],
}: {
  students: Student[];
  stats?: TeacherStudentStats[];
  templates?: HomeworkTemplate[];
}) {
  const router = useRouter();
  const statsById = new Map(stats.map((row) => [row.id, row]));
  const showStats = stats.length > 0;

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [dueAt, setDueAt] = useState("");
  const [tempPassword, setTempPassword] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [assignSuccess, setAssignSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (students.length === 0) {
    return (
      <p className="text-sm text-zinc-500">Пока нет учеников. Создайте первого.</p>
    );
  }

  function toggleRow(studentId: string) {
    setError(null);
    setMessage(null);
    setAssignSuccess(null);
    setTempPassword(null);
    setSelectedTemplateId("");
    setDueAt("");
    setExpandedId((current) => (current === studentId ? null : studentId));
  }

  async function handleAssign(student: Student) {
    if (!selectedTemplateId) {
      setError("Выберите шаблон задания.");
      return;
    }
    const templateTitle =
      templates.find((template) => template.id === selectedTemplateId)?.title ??
      "Задание";
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await assignHomeworkTemplate(selectedTemplateId, {
        student_id: student.id,
        due_at: dueAt ? new Date(dueAt).toISOString() : null,
      });
      setSelectedTemplateId("");
      setDueAt("");
      setAssignSuccess(templateTitle);
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || "Не удалось назначить задание.");
      } else {
        setError("Не удалось назначить задание. Попробуйте позже.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function handleResetPassword(student: Student) {
    setBusy(true);
    setError(null);
    setMessage(null);
    setAssignSuccess(null);
    setTempPassword(null);
    try {
      const result = await resetStudentPassword(student.id);
      setTempPassword(result.temporary_password);
      setMessage("Новый временный пароль (покажите один раз):");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || "Не удалось сбросить пароль.");
      } else {
        setError("Не удалось сбросить пароль. Попробуйте позже.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(student: Student) {
    const confirmed = window.confirm(
      `Удалить ученика «${student.email}»? Войти с этим логином будет нельзя.`,
    );
    if (!confirmed) {
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    setAssignSuccess(null);
    try {
      await deleteStudent(student.id);
      setExpandedId(null);
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || "Не удалось удалить ученика.");
      } else {
        setError("Не удалось удалить ученика. Попробуйте позже.");
      }
    } finally {
      setBusy(false);
    }
  }

  const colSpan = showStats ? 8 : 4;

  return (
    <div className="chem-card overflow-x-auto rounded-lg">
      <table className="w-full min-w-[40rem] text-left text-sm">
        <thead className="chem-table-head">
          <tr>
            <th className="px-4 py-3 font-medium">Ученик</th>
            <th className="px-4 py-3 font-medium">Трек</th>
            <th className="px-4 py-3 font-medium">Онбординг</th>
            {showStats ? (
              <>
                <th className="px-4 py-3 font-medium">Баллы (нед.)</th>
                <th className="px-4 py-3 font-medium">Streak</th>
                <th className="px-4 py-3 font-medium">Задач</th>
                <th className="px-4 py-3 font-medium">Время</th>
                <th className="px-4 py-3 font-medium">Активность</th>
              </>
            ) : (
              <th className="px-4 py-3 font-medium">Создан</th>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-200">
          {students.map((student) => {
            const row = statsById.get(student.id);
            const expanded = expandedId === student.id;
            const panelId = `student-panel-${student.id}`;

            return (
              <Fragment key={student.id}>
                <tr>
                  <td className="px-4 py-3 text-zinc-900">
                    <button
                      type="button"
                      className="text-left font-medium text-chem-teal-dark underline-offset-2 hover:underline focus-visible:underline"
                      aria-expanded={expanded}
                      aria-controls={panelId}
                      onClick={() => toggleRow(student.id)}
                    >
                      {student.email}
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <TrackBadge track={student.track} />
                  </td>
                  <td className="px-4 py-3">
                    {student.is_activated ? (
                      <span className="text-sm font-medium text-chem-teal-dark">
                        Активен
                      </span>
                    ) : (
                      <span className="text-sm text-zinc-500">Не активирован</span>
                    )}
                  </td>
                  {showStats ? (
                    <>
                      <td className="px-4 py-3 text-zinc-900">
                        {row?.week_points ?? 0}
                        <span className="text-xs text-zinc-500">
                          {" "}
                          / {row?.total_points ?? 0}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-zinc-900">
                        {row?.streak ?? 0}
                      </td>
                      <td className="px-4 py-3 text-zinc-900">
                        {row?.tasks_solved ?? 0}
                      </td>
                      <td className="px-4 py-3 text-zinc-900">
                        {formatTotalMinutes(row?.total_minutes ?? 0)}
                      </td>
                      <td className="px-4 py-3 text-zinc-500">
                        {formatActiveDate(row?.last_active_date ?? null)}
                      </td>
                    </>
                  ) : (
                    <td className="px-4 py-3 text-zinc-500">
                      {formatDate(student.created_at)}
                    </td>
                  )}
                </tr>
                {expanded ? (
                  <tr>
                    <td colSpan={colSpan} className="bg-zinc-50 px-4 py-4">
                      <div
                        id={panelId}
                        className="flex max-w-xl flex-col gap-4"
                        role="region"
                        aria-label={`Действия для ${student.email}`}
                      >
                        <div className="flex flex-col gap-2">
                          <h3 className="text-sm font-semibold text-zinc-900">
                            Назначить задание
                          </h3>
                          {assignSuccess ? (
                            <div
                              role="status"
                              className="chem-callout chem-callout-remember flex items-start justify-between gap-3"
                            >
                              <p className="text-sm font-medium text-chem-teal-dark">
                                Назначено: «{assignSuccess}»
                              </p>
                              <button
                                type="button"
                                onClick={() => setAssignSuccess(null)}
                                className="shrink-0 rounded px-1.5 text-sm font-medium text-chem-teal-dark hover:bg-white/60"
                                aria-label="Скрыть уведомление"
                              >
                                Закрыть
                              </button>
                            </div>
                          ) : null}
                          {templates.length === 0 ? (
                            <p className="text-sm text-zinc-500">
                              Нет шаблонов. Создайте задание во вкладке «Задания».
                            </p>
                          ) : (
                            <>
                              <label
                                htmlFor={`assign-template-${student.id}`}
                                className="text-sm font-medium text-zinc-700"
                              >
                                Шаблон
                              </label>
                              <select
                                id={`assign-template-${student.id}`}
                                value={selectedTemplateId}
                                onChange={(e) =>
                                  setSelectedTemplateId(e.target.value)
                                }
                                disabled={busy}
                                className="chem-input rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 disabled:opacity-60"
                              >
                                <option value="">Выберите шаблон…</option>
                                {templates.map((template) => (
                                  <option key={template.id} value={template.id}>
                                    {template.title}
                                  </option>
                                ))}
                              </select>
                              <label
                                htmlFor={`assign-due-${student.id}`}
                                className="text-sm font-medium text-zinc-700"
                              >
                                Срок (необязательно)
                              </label>
                              <input
                                id={`assign-due-${student.id}`}
                                type="datetime-local"
                                value={dueAt}
                                onChange={(e) => setDueAt(e.target.value)}
                                disabled={busy}
                                className="chem-input rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 disabled:opacity-60"
                              />
                              <button
                                type="button"
                                disabled={busy || !selectedTemplateId}
                                onClick={() => handleAssign(student)}
                                className="chem-btn-primary w-fit px-4 py-2 disabled:opacity-60"
                              >
                                Назначить
                              </button>
                            </>
                          )}
                        </div>

                        <div className="flex flex-wrap gap-2">
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => handleResetPassword(student)}
                            className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm font-medium text-zinc-800 hover:bg-zinc-100 disabled:opacity-60"
                          >
                            Сбросить пароль
                          </button>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => handleDelete(student)}
                            className="rounded-md border border-[var(--chem-crimson)]/40 bg-white px-3 py-2 text-sm font-medium text-[var(--chem-crimson)] hover:bg-red-50 disabled:opacity-60"
                          >
                            Удалить ученика
                          </button>
                        </div>

                        {error ? (
                          <p
                            role="alert"
                            className="text-sm text-[var(--chem-crimson)]"
                          >
                            {error}
                          </p>
                        ) : null}
                        {message ? (
                          <p role="status" className="text-sm text-zinc-700">
                            {message}
                            {tempPassword ? (
                              <>
                                {" "}
                                <code className="rounded bg-zinc-200 px-1.5 py-0.5 font-mono text-sm">
                                  {tempPassword}
                                </code>
                              </>
                            ) : null}
                          </p>
                        ) : null}
                      </div>
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
