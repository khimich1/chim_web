"use client";

import { useCallback, useMemo, useState, type RefObject } from "react";

import { SidePanelShell } from "@/components/students/SidePanelShell";
import { ApiError } from "@/lib/api/client";
import {
  deleteTeacherGroup,
  renameTeacherGroup,
  replaceTeacherGroupMembers,
  type StudentGroupDetail,
} from "@/lib/api/groups";
import { assignHomeworkTemplate } from "@/lib/api/templates";
import type { HomeworkTemplate, Student } from "@/lib/api/types";

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
    try {
      const created = await assignHomeworkTemplate(templateId, {
        group_id: group.id,
      });
      setTemplateId("");
      setAssignSuccess(
        `«${templateTitle}» — назначено ученикам: ${created.length}`,
      );
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
