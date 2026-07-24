"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiError } from "@/lib/api/client";
import {
  createTeacherGroup,
  deleteTeacherGroup,
  getTeacherGroup,
  listTeacherGroups,
  renameTeacherGroup,
  replaceTeacherGroupMembers,
  type StudentGroupDetail,
  type StudentGroupSummary,
} from "@/lib/api/groups";
import { assignHomeworkTemplate } from "@/lib/api/templates";
import type { HomeworkTemplate, Student } from "@/lib/api/types";

export function GroupsPanel({
  students,
  templates = [],
}: {
  students: Student[];
  templates?: HomeworkTemplate[];
}) {
  const [groups, setGroups] = useState<StudentGroupSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<StudentGroupDetail | null>(null);
  const [allDetails, setAllDetails] = useState<StudentGroupDetail[]>([]);
  const [draftName, setDraftName] = useState("");
  const [draftMemberIds, setDraftMemberIds] = useState<string[]>([]);
  const [templateId, setTemplateId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [assignSuccess, setAssignSuccess] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const refreshGroups = useCallback(async () => {
    const listed = await listTeacherGroups();
    setGroups(listed);
    const details = await Promise.all(
      listed.map((group) => getTeacherGroup(group.id)),
    );
    setAllDetails(details);
    return { listed, details };
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { listed, details } = await refreshGroups();
        if (cancelled) {
          return;
        }
        if (listed.length > 0) {
          const first = details[0];
          setSelectedId(first.id);
          setDetail(first);
          setDraftName(first.name);
          setDraftMemberIds(first.members.map((m) => m.id));
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiError
              ? err.message || "Не удалось загрузить группы."
              : "Не удалось загрузить группы.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshGroups]);

  const membershipByStudent = useMemo(() => {
    const map = new Map<string, { groupId: string; groupName: string }>();
    for (const group of allDetails) {
      for (const member of group.members) {
        map.set(member.id, { groupId: group.id, groupName: group.name });
      }
    }
    return map;
  }, [allDetails]);

  const selectableStudents = useMemo(() => {
    if (!selectedId) {
      return [];
    }
    return students.filter((student) => {
      const membership = membershipByStudent.get(student.id);
      return !membership || membership.groupId === selectedId;
    });
  }, [students, membershipByStudent, selectedId]);

  const blockedStudents = useMemo(() => {
    if (!selectedId) {
      return [];
    }
    return students.filter((student) => {
      const membership = membershipByStudent.get(student.id);
      return membership != null && membership.groupId !== selectedId;
    });
  }, [students, membershipByStudent, selectedId]);

  async function selectGroup(groupId: string) {
    setError(null);
    setMessage(null);
    setAssignSuccess(null);
    setTemplateId("");
    setBusy(true);
    try {
      const next = await getTeacherGroup(groupId);
      setSelectedId(groupId);
      setDetail(next);
      setDraftName(next.name);
      setDraftMemberIds(next.members.map((m) => m.id));
      setAllDetails((prev) => {
        const others = prev.filter((g) => g.id !== groupId);
        return [...others, next];
      });
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message || "Не удалось открыть группу."
          : "Не удалось открыть группу.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleCreate() {
    setBusy(true);
    setError(null);
    setMessage(null);
    setAssignSuccess(null);
    try {
      const created = await createTeacherGroup({});
      const { details } = await refreshGroups();
      const next = details.find((g) => g.id === created.id) ?? created;
      setSelectedId(next.id);
      setDetail(next);
      setDraftName(next.name);
      setDraftMemberIds(next.members.map((m) => m.id));
      setMessage(`Создана группа «${next.name}».`);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message || "Не удалось создать группу."
          : "Не удалось создать группу.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleRename() {
    if (!selectedId || !draftName.trim()) {
      setError("Введите название группы.");
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await renameTeacherGroup(selectedId, draftName.trim());
      setDetail(updated);
      setDraftName(updated.name);
      await refreshGroups();
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
    if (!selectedId) {
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await replaceTeacherGroupMembers(
        selectedId,
        draftMemberIds,
      );
      setDetail(updated);
      setDraftMemberIds(updated.members.map((m) => m.id));
      await refreshGroups();
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
    if (!selectedId) {
      return;
    }
    if (!templateId) {
      setError("Выберите шаблон задания.");
      return;
    }
    if (!detail || detail.member_count === 0) {
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
        group_id: selectedId,
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
    if (!selectedId || !detail) {
      return;
    }
    const confirmed = window.confirm(
      `Удалить группу «${detail.name}»? Несданные групповые задания будут отозваны.`,
    );
    if (!confirmed) {
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    setAssignSuccess(null);
    try {
      await deleteTeacherGroup(selectedId);
      const { listed, details } = await refreshGroups();
      if (listed.length === 0) {
        setSelectedId(null);
        setDetail(null);
        setDraftName("");
        setDraftMemberIds([]);
      } else {
        const next = details[0];
        setSelectedId(next.id);
        setDetail(next);
        setDraftName(next.name);
        setDraftMemberIds(next.members.map((m) => m.id));
      }
      setMessage("Группа удалена.");
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

  function toggleMember(studentId: string) {
    setDraftMemberIds((current) =>
      current.includes(studentId)
        ? current.filter((id) => id !== studentId)
        : [...current, studentId],
    );
  }

  if (loading) {
    return <p className="text-sm text-zinc-500">Загрузка групп…</p>;
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-zinc-900">
          Группы ({groups.length})
        </h2>
        <button
          type="button"
          disabled={busy}
          onClick={() => void handleCreate()}
          className="chem-btn-primary px-4 py-2 disabled:opacity-60"
        >
          Создать группу
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
        </p>
      ) : null}

      {groups.length === 0 ? (
        <p className="text-sm text-zinc-500">
          Групп пока нет. Создайте первую — имя будет «Группа 1».
        </p>
      ) : (
        <ul className="flex flex-col gap-2" aria-label="Список групп">
          {groups.map((group) => (
            <li key={group.id}>
              <button
                type="button"
                onClick={() => void selectGroup(group.id)}
                aria-pressed={selectedId === group.id}
                className={`flex w-full items-center justify-between rounded-lg border px-4 py-3 text-left text-sm transition ${
                  selectedId === group.id
                    ? "border-chem-teal bg-white shadow-sm"
                    : "border-zinc-200 bg-zinc-50 hover:bg-white"
                }`}
              >
                <span className="font-medium text-zinc-900">{group.name}</span>
                <span className="text-zinc-500">
                  {group.member_count} уч.
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {detail && selectedId ? (
        <section
          className="chem-card flex flex-col gap-5 rounded-lg p-5"
          aria-label={`Группа ${detail.name}`}
        >
          <div className="flex flex-col gap-2">
            <label
              htmlFor={`group-name-${detail.id}`}
              className="text-sm font-medium text-zinc-700"
            >
              Название
            </label>
            <div className="flex flex-wrap gap-2">
              <input
                id={`group-name-${detail.id}`}
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
          </div>

          <div className="flex flex-col gap-2">
            <h3 className="text-sm font-semibold text-zinc-900">Состав</h3>
            {selectableStudents.length === 0 && blockedStudents.length === 0 ? (
              <p className="text-sm text-zinc-500">Нет учеников для выбора.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {selectableStudents.map((student) => (
                  <li key={student.id}>
                    <label className="flex items-center gap-2 text-sm text-zinc-800">
                      <input
                        type="checkbox"
                        checked={draftMemberIds.includes(student.id)}
                        onChange={() => toggleMember(student.id)}
                      />
                      <span>
                        {student.email}{" "}
                        <span className="text-zinc-500">
                          ({student.track === "ege" ? "ЕГЭ" : "ОГЭ"})
                        </span>
                      </span>
                    </label>
                  </li>
                ))}
              </ul>
            )}
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
          </div>

          <div className="flex flex-col gap-2">
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
                  htmlFor={`group-assign-${detail.id}`}
                  className="text-sm font-medium text-zinc-700"
                >
                  Шаблон
                </label>
                <select
                  id={`group-assign-${detail.id}`}
                  value={templateId}
                  onChange={(e) => setTemplateId(e.target.value)}
                  disabled={busy || detail.member_count === 0}
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
                  disabled={busy || detail.member_count === 0 || !templateId}
                  onClick={() => void handleAssign()}
                  className="chem-btn-primary w-fit px-4 py-2 disabled:opacity-60"
                >
                  Назначить группе
                </button>
                {detail.member_count === 0 ? (
                  <p className="text-xs text-zinc-500">
                    Добавьте хотя бы одного ученика, чтобы назначить задание.
                  </p>
                ) : null}
              </>
            )}
          </div>

          <button
            type="button"
            disabled={busy}
            onClick={() => void handleDelete()}
            className="w-fit rounded-md border border-[var(--chem-crimson)]/40 bg-white px-3 py-2 text-sm font-medium text-[var(--chem-crimson)] hover:bg-red-50 disabled:opacity-60"
          >
            Удалить группу
          </button>
        </section>
      ) : null}
    </div>
  );
}
