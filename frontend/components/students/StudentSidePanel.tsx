"use client";

import { useCallback, useEffect, useState, type RefObject } from "react";
import { useRouter } from "next/navigation";

import { SidePanelShell } from "@/components/students/SidePanelShell";
import { TrackBadge } from "@/components/ui/TrackBadge";
import { ApiError } from "@/lib/api/client";
import {
  cancelHomework,
  listHomework,
  restoreHomework,
} from "@/lib/api/homework";
import {
  deleteStudent,
  resetStudentPassword,
} from "@/lib/api/students";
import { assignHomeworkTemplate } from "@/lib/api/templates";
import { formatTotalMinutes } from "@/lib/format-duration";
import type {
  HomeworkAssignment,
  HomeworkStatus,
  HomeworkTemplate,
  Student,
  TeacherStudentStats,
} from "@/lib/api/types";

const STATUS_LABEL: Record<HomeworkStatus, string> = {
  assigned: "Назначено",
  in_progress: "В процессе",
  submitted: "Сдано",
  reviewed: "Проверено",
  cancelled: "Отменено",
};

const UNDO_MS = 30_000;

function canCancelStatus(status: HomeworkStatus): boolean {
  return status === "assigned" || status === "in_progress";
}

function TrashIcon() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 20 20"
      className="h-4 w-4"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M6.5 6.5v8m3.5-8v8m3.5-8v8M4 5.5h12m-1 0-.7 10.2A1.5 1.5 0 0 1 12.8 17H7.2a1.5 1.5 0 0 1-1.5-1.3L5 5.5m3-.8A1.5 1.5 0 0 1 9.5 3h1A1.5 1.5 0 0 1 12 4.7V5.5"
      />
    </svg>
  );
}

function formatDue(iso: string | null): string {
  if (!iso) {
    return "без срока";
  }
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
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

export function StudentSidePanel({
  student,
  stats = null,
  templates,
  open,
  onClose,
  returnFocusRef,
}: {
  student: Student;
  stats?: TeacherStudentStats | null;
  templates: HomeworkTemplate[];
  open: boolean;
  onClose: () => void;
  returnFocusRef?: RefObject<HTMLElement | null>;
}) {
  const router = useRouter();
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [dueAt, setDueAt] = useState("");
  const [tempPassword, setTempPassword] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [assignSuccess, setAssignSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [homework, setHomework] = useState<HomeworkAssignment[]>([]);
  const [homeworkLoading, setHomeworkLoading] = useState(true);
  const [homeworkError, setHomeworkError] = useState<string | null>(null);
  const [undo, setUndo] = useState<{
    assignmentId: string;
    title: string;
  } | null>(null);

  const loadHomework = useCallback(async () => {
    setHomeworkError(null);
    try {
      const all = await listHomework();
      setHomework(all.filter((row) => row.student_id === student.id));
    } catch (err) {
      setHomework([]);
      setHomeworkError(
        err instanceof ApiError
          ? err.message || "Не удалось загрузить историю ДЗ."
          : "Не удалось загрузить историю ДЗ.",
      );
    } finally {
      setHomeworkLoading(false);
    }
  }, [student.id]);

  useEffect(() => {
    if (!undo) {
      return;
    }
    const timer = window.setTimeout(() => setUndo(null), UNDO_MS);
    return () => window.clearTimeout(timer);
  }, [undo]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const all = await listHomework();
        if (cancelled) {
          return;
        }
        setHomework(all.filter((row) => row.student_id === student.id));
        setHomeworkError(null);
      } catch (err) {
        if (cancelled) {
          return;
        }
        setHomework([]);
        setHomeworkError(
          err instanceof ApiError
            ? err.message || "Не удалось загрузить историю ДЗ."
            : "Не удалось загрузить историю ДЗ.",
        );
      } finally {
        if (!cancelled) {
          setHomeworkLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [student.id]);

  async function handleAssign() {
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
      await loadHomework();
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

  async function handleResetPassword() {
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

  async function handleDelete() {
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
      onClose();
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

  async function handleCancel(row: HomeworkAssignment) {
    setBusy(true);
    setError(null);
    setAssignSuccess(null);
    try {
      await cancelHomework(row.id, "single");
      setUndo({ assignmentId: row.id, title: row.title });
      await loadHomework();
      router.refresh();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message || "Не удалось отозвать задание."
          : "Не удалось отозвать задание.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleRestore() {
    if (!undo) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await restoreHomework(undo.assignmentId, "single");
      setUndo(null);
      await loadHomework();
      router.refresh();
    } catch (err) {
      setUndo(null);
      setError(
        err instanceof ApiError
          ? err.message || "Не удалось вернуть задание (окно 30 с истекло)."
          : "Не удалось вернуть задание.",
      );
    } finally {
      setBusy(false);
    }
  }

  const openHomework = homework.filter((row) => row.status === "in_progress");

  return (
    <SidePanelShell
      open={open}
      title={student.email}
      onClose={onClose}
      returnFocusRef={returnFocusRef}
    >
      <div className="flex flex-col gap-6">
        <section className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <TrackBadge track={student.track} />
            {student.is_activated ? (
              <span className="text-sm font-medium text-chem-teal-dark">
                Активен
              </span>
            ) : (
              <span className="text-sm text-zinc-500">Не активирован</span>
            )}
          </div>
          {stats ? (
            <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
              <div>
                <dt className="text-zinc-500">Баллы (нед.)</dt>
                <dd className="font-medium text-zinc-900">
                  {stats.week_points}{" "}
                  <span className="text-xs text-zinc-500">
                    / {stats.total_points}
                  </span>
                </dd>
              </div>
              <div>
                <dt className="text-zinc-500">Streak</dt>
                <dd className="font-medium text-zinc-900">{stats.streak}</dd>
              </div>
              <div>
                <dt className="text-zinc-500">Задач</dt>
                <dd className="font-medium text-zinc-900">
                  {stats.tasks_solved}
                </dd>
              </div>
              <div>
                <dt className="text-zinc-500">Время</dt>
                <dd className="font-medium text-zinc-900">
                  {formatTotalMinutes(stats.total_minutes)}
                </dd>
              </div>
              <div className="col-span-2">
                <dt className="text-zinc-500">Активность</dt>
                <dd className="font-medium text-zinc-900">
                  {formatActiveDate(stats.last_active_date)}
                </dd>
              </div>
            </dl>
          ) : null}
        </section>

        <section className="flex flex-col gap-2" aria-labelledby="open-hw-heading">
          <h3
            id="open-hw-heading"
            className="text-sm font-semibold text-zinc-900"
          >
            Открытые
          </h3>
          {homeworkLoading ? (
            <p className="text-sm text-zinc-500">Загрузка…</p>
          ) : openHomework.length === 0 ? (
            <p className="text-sm text-zinc-500">Нет заданий в процессе.</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {openHomework.map((row) => (
                <li
                  key={row.id}
                  className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm"
                >
                  <p className="font-medium text-zinc-900">{row.title}</p>
                  <p className="text-zinc-500">
                    {STATUS_LABEL[row.status]} · {formatDue(row.due_at)}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="flex flex-col gap-2" aria-labelledby="hw-history-heading">
          <h3
            id="hw-history-heading"
            className="text-sm font-semibold text-zinc-900"
          >
            История заданий
          </h3>
          {homeworkError ? (
            <p role="alert" className="text-sm text-[var(--chem-crimson)]">
              {homeworkError}
            </p>
          ) : null}
          {homeworkLoading ? (
            <p className="text-sm text-zinc-500">Загрузка…</p>
          ) : homework.length === 0 ? (
            <p className="text-sm text-zinc-500">Пока нет назначенных заданий.</p>
          ) : (
            <ul className="flex flex-col gap-2" aria-label="История заданий">
              {homework.map((row) => (
                <li
                  key={row.id}
                  className="flex items-start justify-between gap-2 rounded-md border border-zinc-200 px-3 py-2 text-sm"
                >
                  <div className="min-w-0">
                    <p className="font-medium text-zinc-900">{row.title}</p>
                    <p className="text-zinc-500">
                      {row.status === "cancelled" ? (
                        <span className="font-medium text-[var(--chem-crimson)]">
                          Отменено
                        </span>
                      ) : (
                        STATUS_LABEL[row.status]
                      )}{" "}
                      · {formatDue(row.due_at)}
                    </p>
                  </div>
                  {canCancelStatus(row.status) ? (
                    <button
                      type="button"
                      disabled={busy}
                      aria-label={`Отозвать задание «${row.title}»`}
                      onClick={() => void handleCancel(row)}
                      className="shrink-0 rounded p-1.5 text-zinc-500 hover:bg-zinc-100 hover:text-[var(--chem-crimson)] disabled:opacity-60"
                    >
                      <TrashIcon />
                    </button>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </section>

        {undo ? (
          <div
            role="status"
            className="chem-callout chem-callout-remember flex flex-wrap items-center justify-between gap-3"
          >
            <p className="text-sm font-medium text-chem-teal-dark">
              Отозвано: «{undo.title}».
            </p>
            <button
              type="button"
              disabled={busy}
              onClick={() => void handleRestore()}
              className="shrink-0 rounded-md border border-chem-teal/40 bg-white px-3 py-1.5 text-sm font-medium text-chem-teal-dark hover:bg-white/80 disabled:opacity-60"
            >
              Вернуть
            </button>
          </div>
        ) : null}
        <section className="flex flex-col gap-2">
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
                onChange={(e) => setSelectedTemplateId(e.target.value)}
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
                onClick={() => void handleAssign()}
                className="chem-btn-primary w-fit px-4 py-2 disabled:opacity-60"
              >
                Назначить
              </button>
            </>
          )}
        </section>

        <section
          className="flex flex-col gap-2"
          aria-labelledby="ai-dialogs-heading"
        >
          <h3
            id="ai-dialogs-heading"
            className="text-sm font-semibold text-zinc-900"
          >
            Диалоги AI
          </h3>
          <p className="text-sm text-zinc-500">Скоро</p>
        </section>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={() => void handleResetPassword()}
            className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm font-medium text-zinc-800 hover:bg-zinc-100 disabled:opacity-60"
          >
            Сбросить пароль
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => void handleDelete()}
            className="rounded-md border border-[var(--chem-crimson)]/40 bg-white px-3 py-2 text-sm font-medium text-[var(--chem-crimson)] hover:bg-red-50 disabled:opacity-60"
          >
            Удалить ученика
          </button>
        </div>

        {error ? (
          <p role="alert" className="text-sm text-[var(--chem-crimson)]">
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
    </SidePanelShell>
  );
}
