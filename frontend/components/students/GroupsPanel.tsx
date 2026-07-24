"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { GroupSidePanel } from "@/components/students/GroupSidePanel";
import { ApiError } from "@/lib/api/client";
import {
  createTeacherGroup,
  getTeacherGroup,
  listTeacherGroups,
  type StudentGroupDetail,
  type StudentGroupSummary,
} from "@/lib/api/groups";
import type { HomeworkTemplate, Student } from "@/lib/api/types";

export function GroupsPanel({
  students,
  templates = [],
}: {
  students: Student[];
  templates?: HomeworkTemplate[];
}) {
  const [groups, setGroups] = useState<StudentGroupSummary[]>([]);
  const [openGroupId, setOpenGroupId] = useState<string | null>(null);
  const [detail, setDetail] = useState<StudentGroupDetail | null>(null);
  const [allDetails, setAllDetails] = useState<StudentGroupDetail[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const triggerRefs = useRef(new Map<string, HTMLElement>());

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
        await refreshGroups();
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

  async function openGroup(groupId: string, trigger?: HTMLElement | null) {
    if (trigger) {
      triggerRefs.current.set(groupId, trigger);
    }
    setError(null);
    setMessage(null);
    setBusy(true);
    try {
      const next = await getTeacherGroup(groupId);
      setOpenGroupId(groupId);
      setDetail(next);
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

  function closeGroup() {
    setOpenGroupId(null);
    setDetail(null);
  }

  async function handleCreate() {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const created = await createTeacherGroup({});
      const { details } = await refreshGroups();
      const next = details.find((g) => g.id === created.id) ?? created;
      setOpenGroupId(next.id);
      setDetail(next);
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

  async function handleGroupUpdated(updated: StudentGroupDetail) {
    setDetail(updated);
    setAllDetails((prev) => {
      const others = prev.filter((g) => g.id !== updated.id);
      return [...others, updated];
    });
    await refreshGroups();
  }

  async function handleGroupDeleted() {
    closeGroup();
    setBusy(true);
    try {
      await refreshGroups();
      setMessage("Группа удалена.");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message || "Не удалось обновить список групп."
          : "Не удалось обновить список групп.",
      );
    } finally {
      setBusy(false);
    }
  }

  const returnFocusRef = {
    get current() {
      if (!openGroupId) {
        return null;
      }
      return triggerRefs.current.get(openGroupId) ?? null;
    },
  };

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
                onClick={(event) =>
                  void openGroup(group.id, event.currentTarget)
                }
                aria-haspopup="dialog"
                className="flex w-full items-center justify-between rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3 text-left text-sm transition hover:bg-white"
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

      {detail && openGroupId ? (
        <GroupSidePanel
          key={openGroupId}
          group={detail}
          students={students}
          templates={templates}
          membershipByStudent={membershipByStudent}
          open
          onClose={closeGroup}
          onUpdated={(updated) => void handleGroupUpdated(updated)}
          onDeleted={() => void handleGroupDeleted()}
          returnFocusRef={returnFocusRef}
        />
      ) : null}
    </div>
  );
}
