"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type RefObject } from "react";

import { SidePanelShell } from "@/components/students/SidePanelShell";
import { ApiError } from "@/lib/api/client";
import {
  deleteTeacherGroup,
  renameTeacherGroup,
  replaceTeacherGroupMembers,
  type StudentGroupDetail,
} from "@/lib/api/groups";
import {
  cancelHomework,
  listHomework,
  restoreHomework,
} from "@/lib/api/homework";
import { assignHomeworkTemplate } from "@/lib/api/templates";
import type { HomeworkAssignment, HomeworkTemplate, Student } from "@/lib/api/types";
import {
  formatWaveSummary,
  groupHomeworkWaves,
  type GroupHomeworkWave,
} from "@/lib/students/groupHomeworkWaves";

const UNDO_MS = 30_000;

function formatDue(iso: string | null): string {
  if (!iso) {
    return "без срока";
  }
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(iso));
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

export function GroupSidePanel({
  group,
  students,
  templates,
  membershipByStudent,
  open,
  onClose,
  onUpdated,
  onDeleted,
  returnFocusRef,
}: {
  group: StudentGroupDetail;
  students: Student[];
  templates: HomeworkTemplate[];
  membershipByStudent: Map<string, { groupId: string; groupName: string }>;
  open: boolean;
  onClose: () => void;
  onUpdated: (detail: StudentGroupDetail) => void;
  onDeleted: () => void;
  returnFocusRef?: RefObject<HTMLElement | null>;
}) {
  const [draftName, setDraftName] = useState(group.name);
  const [draftMemberIds, setDraftMemberIds] = useState(
    group.members.map((m) => m.id),
  );
  const [selectedInGroup, setSelectedInGroup] = useState<string | null>(null);
  const [selectedFree, setSelectedFree] = useState<string | null>(null);
  const [templateId, setTemplateId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [assignSuccess, setAssignSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [homework, setHomework] = useState<HomeworkAssignment[]>([]);
  const [homeworkLoading, setHomeworkLoading] = useState(true);
  const [homeworkError, setHomeworkError] = useState<string | null>(null);
  const [undo, setUndo] = useState<{
    anchorId: string;
    title: string;
    cancelledCount: number;
    skippedSubmittedCount: number;
  } | null>(null);

  const loadHomework = useCallback(async () => {
    setHomeworkError(null);
    try {
      const all = await listHomework();
      setHomework(all.filter((row) => row.source_group_id === group.id));
    } catch (err) {
      setHomework([]);
      setHomeworkError(
        err instanceof ApiError
          ? err.message || "Не удалось загрузить историю раздач."
          : "Не удалось загрузить историю раздач.",
      );
    } finally {
      setHomeworkLoading(false);
    }
  }, [group.id]);

  useEffect(() => {
    if (!open) {
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const all = await listHomework();
        if (cancelled) {
          return;
        }
        setHomework(all.filter((row) => row.source_group_id === group.id));
        setHomeworkError(null);
      } catch (err) {
        if (cancelled) {
          return;
        }
        setHomework([]);
        setHomeworkError(
          err instanceof ApiError
            ? err.message || "Не удалось загрузить историю раздач."
            : "Не удалось загрузить историю раздач.",
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
  }, [open, group.id]);

  useEffect(() => {
    if (!undo) {
      return;
    }
    const timer = window.setTimeout(() => setUndo(null), UNDO_MS);
    return () => window.clearTimeout(timer);
  }, [undo]);

  const waves = useMemo(
    () => groupHomeworkWaves(homework, group.id),
    [homework, group.id],
  );

  const inGroupStudents = useMemo(() => {
    return students.filter((student) => draftMemberIds.includes(student.id));
  }, [students, draftMemberIds]);

  const freeStudents = useMemo(() => {
    return students.filter((student) => {
      const membership = membershipByStudent.get(student.id);
      const inDraft = draftMemberIds.includes(student.id);
      if (inDraft) {
        return false;
      }
      return !membership || membership.groupId === group.id;
    });
  }, [students, membershipByStudent, draftMemberIds, group.id]);

  const blockedStudents = useMemo(() => {
    return students.filter((student) => {
      const membership = membershipByStudent.get(student.id);
      return membership != null && membership.groupId !== group.id;
    });
  }, [students, membershipByStudent, group.id]);

  const addToGroup = useCallback((studentId: string) => {
    setDraftMemberIds((current) =>
      current.includes(studentId) ? current : [...current, studentId],
    );
    setSelectedFree(null);
  }, []);

  const removeFromGroup = useCallback((studentId: string) => {
    setDraftMemberIds((current) => current.filter((id) => id !== studentId));
    setSelectedInGroup(null);
  }, []);

  async function handleRename() {
    if (!draftName.trim()) {
      setError("Введите название группы.");
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await renameTeacherGroup(group.id, draftName.trim());
      onUpdated(updated);
      setDraftName(updated.name);
      setMessage("Название сохранено.");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message || "Не удалось переименовать группу."
          : "Не удалось переименовать группу.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleSaveMembers() {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await replaceTeacherGroupMembers(
        group.id,
        draftMemberIds,
      );
      onUpdated(updated);
      setDraftMemberIds(updated.members.map((m) => m.id));
      setMessage("Состав группы сохранён.");
    } catch (err) {
      if (err instanceof ApiError) {
        if (
          err.status === 422 &&
          /another group|другой групп/i.test(err.message)
        ) {
          setError(
            "Ученик уже в другой группе. Сначала уберите его там, затем добавьте сюда.",
          );
        } else {
          setError(err.message || "Не удалось сохранить состав.");
        }
      } else {
        setError("Не удалось сохранить состав.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function handleAssign() {
    if (!templateId) {
      setError("Выберите шаблон задания.");
      return;
    }
    if (group.member_count === 0) {
      setError("Нельзя назначить пустой группе. Добавьте учеников.");
      return;
    }
    const templateTitle =
      templates.find((template) => template.id === templateId)?.title ??
      "Задание";
    setBusy(true);
    setError(null);
    setMessage(null);
    setUndo(null);
    try {
      const created = await assignHomeworkTemplate(templateId, {
        group_id: group.id,
      });
      setTemplateId("");
      setAssignSuccess(
        `«${templateTitle}» — назначено ученикам: ${created.length}`,
      );
      await loadHomework();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || "Не удалось назначить задание группе.");
      } else {
        setError("Не удалось назначить задание группе.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function handleCancelWave(wave: GroupHomeworkWave) {
    setBusy(true);
    setError(null);
    setAssignSuccess(null);
    try {
      const result = await cancelHomework(wave.anchorId, "wave");
      setUndo({
        anchorId: wave.anchorId,
        title: wave.title,
        cancelledCount: result.cancelled_ids.length,
        skippedSubmittedCount: result.skipped_submitted_count,
      });
      await loadHomework();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message || "Не удалось отозвать раздачу."
          : "Не удалось отозвать раздачу.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleRestoreWave() {
    if (!undo) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await restoreHomework(undo.anchorId, "wave");
      setUndo(null);
      await loadHomework();
    } catch (err) {
      setUndo(null);
      setError(
        err instanceof ApiError
          ? err.message || "Не удалось вернуть раздачу (окно 30 с истекло)."
          : "Не удалось вернуть раздачу.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    const confirmed = window.confirm(
      `Удалить группу «${group.name}»? Несданные групповые задания будут отозваны.`,
    );
    if (!confirmed) {
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    setAssignSuccess(null);
    setUndo(null);
    try {
      await deleteTeacherGroup(group.id);
      onDeleted();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message || "Не удалось удалить группу."
          : "Не удалось удалить группу.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <SidePanelShell
      open={open}
      title={group.name}
      onClose={onClose}
      returnFocusRef={returnFocusRef}
    >
      <div className="flex flex-col gap-6">
        {error ? (
          <p role="alert" className="text-sm text-[var(--chem-crimson)]">
            {error}
          </p>
        ) : null}
        {message ? (
          <p role="status" className="text-sm text-zinc-700">
            {message}
          </p>
        ) : null}

        <section className="flex flex-col gap-2">
          <label
            htmlFor={`group-name-${group.id}`}
            className="text-sm font-medium text-zinc-700"
          >
            Название
          </label>
          <div className="flex flex-wrap gap-2">
            <input
              id={`group-name-${group.id}`}
              value={draftName}
              onChange={(e) => setDraftName(e.target.value)}
              className="chem-input min-w-[12rem] flex-1 rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900"
            />
            <button
              type="button"
              disabled={busy}
              onClick={() => void handleRename()}
              className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm font-medium text-zinc-800 hover:bg-zinc-100 disabled:opacity-60"
            >
              Сохранить имя
            </button>
          </div>
        </section>

        <section className="flex flex-col gap-3" aria-label="Состав группы">
          <h3 className="text-sm font-semibold text-zinc-900">Состав</h3>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-[1fr_auto_1fr]">
            <div className="flex flex-col gap-2">
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                В группе
              </p>
              <ul
                className="min-h-[8rem] rounded-md border border-zinc-200 bg-zinc-50 p-2"
                aria-label="В группе"
              >
                {inGroupStudents.length === 0 ? (
                  <li className="px-2 py-1 text-sm text-zinc-500">Пусто</li>
                ) : (
                  inGroupStudents.map((student) => (
                    <li key={student.id}>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedInGroup(student.id);
                          setSelectedFree(null);
                        }}
                        onDoubleClick={() => removeFromGroup(student.id)}
                        className={`w-full rounded px-2 py-1.5 text-left text-sm ${
                          selectedInGroup === student.id
                            ? "bg-chem-teal/15 font-medium text-chem-teal-dark"
                            : "text-zinc-800 hover:bg-white"
                        }`}
                      >
                        {student.email}{" "}
                        <span className="text-zinc-500">
                          ({student.track === "ege" ? "ЕГЭ" : "ОГЭ"})
                        </span>
                      </button>
                    </li>
                  ))
                )}
              </ul>
            </div>

            <div className="flex flex-row items-center justify-center gap-2 sm:flex-col">
              <button
                type="button"
                disabled={busy || !selectedFree}
                onClick={() => selectedFree && addToGroup(selectedFree)}
                className="rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-800 hover:bg-zinc-100 disabled:opacity-60"
                aria-label="Добавить в группу"
              >
                ←
              </button>
              <button
                type="button"
                disabled={busy || !selectedInGroup}
                onClick={() =>
                  selectedInGroup && removeFromGroup(selectedInGroup)
                }
                className="rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-sm font-medium text-zinc-800 hover:bg-zinc-100 disabled:opacity-60"
                aria-label="Убрать из группы"
              >
                →
              </button>
            </div>

            <div className="flex flex-col gap-2">
              <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                Свободные
              </p>
              <ul
                className="min-h-[8rem] rounded-md border border-zinc-200 bg-zinc-50 p-2"
                aria-label="Свободные"
              >
                {freeStudents.length === 0 ? (
                  <li className="px-2 py-1 text-sm text-zinc-500">Пусто</li>
                ) : (
                  freeStudents.map((student) => (
                    <li key={student.id}>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedFree(student.id);
                          setSelectedInGroup(null);
                        }}
                        onDoubleClick={() => addToGroup(student.id)}
                        className={`w-full rounded px-2 py-1.5 text-left text-sm ${
                          selectedFree === student.id
                            ? "bg-chem-teal/15 font-medium text-chem-teal-dark"
                            : "text-zinc-800 hover:bg-white"
                        }`}
                      >
                        {student.email}{" "}
                        <span className="text-zinc-500">
                          ({student.track === "ege" ? "ЕГЭ" : "ОГЭ"})
                        </span>
                      </button>
                    </li>
                  ))
                )}
              </ul>
            </div>
          </div>

          {blockedStudents.length > 0 ? (
            <p className="text-xs text-zinc-500">
              Уже в других группах (сначала уберите там):{" "}
              {blockedStudents
                .map((s) => {
                  const m = membershipByStudent.get(s.id);
                  return `${s.email} → ${m?.groupName ?? "?"}`;
                })
                .join("; ")}
            </p>
          ) : null}

          <button
            type="button"
            disabled={busy}
            onClick={() => void handleSaveMembers()}
            className="chem-btn-primary w-fit px-4 py-2 disabled:opacity-60"
          >
            Сохранить состав
          </button>
        </section>

        <section
          className="flex flex-col gap-2"
          aria-labelledby="group-hw-history-heading"
        >
          <h3
            id="group-hw-history-heading"
            className="text-sm font-semibold text-zinc-900"
          >
            История раздач
          </h3>
          {homeworkError ? (
            <p role="alert" className="text-sm text-[var(--chem-crimson)]">
              {homeworkError}
            </p>
          ) : null}
          {homeworkLoading ? (
            <p className="text-sm text-zinc-500">Загрузка…</p>
          ) : waves.length === 0 ? (
            <p className="text-sm text-zinc-500">Пока нет раздач этой группе.</p>
          ) : (
            <ul className="flex flex-col gap-2" aria-label="История раздач">
              {waves.map((wave) => (
                <li
                  key={wave.assignBatchId}
                  className="flex items-start justify-between gap-2 rounded-md border border-zinc-200 px-3 py-2 text-sm"
                >
                  <div className="min-w-0">
                    <Link
                      href={`/teacher/homework/${wave.anchorId}`}
                      className="font-medium text-zinc-900 hover:underline"
                    >
                      {wave.title}
                    </Link>
                    <p className="text-zinc-500">
                      {wave.allCancelled ? (
                        <span className="font-medium text-[var(--chem-crimson)]">
                          Отозвано
                        </span>
                      ) : (
                        formatWaveSummary(wave)
                      )}{" "}
                      · {formatDue(wave.dueAt)}
                    </p>
                  </div>
                  {wave.canCancel ? (
                    <button
                      type="button"
                      disabled={busy}
                      aria-label={`Отозвать задание «${wave.title}»`}
                      onClick={() => void handleCancelWave(wave)}
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
              Отозвано: «{undo.title}» — {undo.cancelledCount}
              {undo.skippedSubmittedCount > 0
                ? ` (сдано не тронуто: ${undo.skippedSubmittedCount})`
                : ""}
              .
            </p>
            <button
              type="button"
              disabled={busy}
              onClick={() => void handleRestoreWave()}
              className="shrink-0 rounded-md border border-chem-teal/40 bg-white px-3 py-1.5 text-sm font-medium text-chem-teal-dark hover:bg-white/80 disabled:opacity-60"
            >
              Вернуть
            </button>
          </div>
        ) : null}

        <section className="flex flex-col gap-2">
          <h3 className="text-sm font-semibold text-zinc-900">
            Назначить задание группе
          </h3>
          {assignSuccess ? (
            <div
              role="status"
              className="chem-callout chem-callout-remember flex items-start justify-between gap-3"
            >
              <p className="text-sm font-medium text-chem-teal-dark">
                Назначено: {assignSuccess}
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
                htmlFor={`group-assign-${group.id}`}
                className="text-sm font-medium text-zinc-700"
              >
                Шаблон
              </label>
              <select
                id={`group-assign-${group.id}`}
                value={templateId}
                onChange={(e) => setTemplateId(e.target.value)}
                disabled={busy || group.member_count === 0}
                className="chem-input rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900 disabled:opacity-60"
              >
                <option value="">Выберите шаблон…</option>
                {templates.map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.title}
                  </option>
                ))}
              </select>
              <button
                type="button"
                disabled={busy || group.member_count === 0 || !templateId}
                onClick={() => void handleAssign()}
                className="chem-btn-primary w-fit px-4 py-2 disabled:opacity-60"
              >
                Назначить группе
              </button>
              {group.member_count === 0 ? (
                <p className="text-xs text-zinc-500">
                  Добавьте хотя бы одного ученика, чтобы назначить задание.
                </p>
              ) : null}
            </>
          )}
        </section>

        <button
          type="button"
          disabled={busy}
          onClick={() => void handleDelete()}
          className="w-fit rounded-md border border-[var(--chem-crimson)]/40 bg-white px-3 py-2 text-sm font-medium text-[var(--chem-crimson)] hover:bg-red-50 disabled:opacity-60"
        >
          Удалить группу
        </button>
      </div>
    </SidePanelShell>
  );
}
