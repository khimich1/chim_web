"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { createHomework } from "@/lib/api/homework";
import { ApiError } from "@/lib/api/client";
import type { CustomTask, HomeworkItem, Student, Track } from "@/lib/api/types";

import {
  estimateTestByTypeSteps,
  formatHomeworkItemLabel,
  typeNumbersForTrack,
} from "./homework-utils";

type HomeworkKind = HomeworkItem["kind"];

export type TeacherThemeOption = {
  id: string;
  title: string;
  tasks: CustomTask[];
};

export function HomeworkForm({
  students,
  topics,
  variantsByTrack,
  teacherThemes,
}: {
  students: Student[];
  topics: string[];
  variantsByTrack: Record<Track, string[]>;
  teacherThemes: TeacherThemeOption[];
}) {
  const router = useRouter();
  const [studentId, setStudentId] = useState(students[0]?.id ?? "");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [items, setItems] = useState<HomeworkItem[]>([]);
  const [draftKind, setDraftKind] = useState<HomeworkKind>("lecture");
  const [draftTopic, setDraftTopic] = useState(topics[0] ?? "");
  const [draftVariant, setDraftVariant] = useState("");
  const [draftTypes, setDraftTypes] = useState<number[]>([10, 11]);
  const [draftThemeId, setDraftThemeId] = useState(teacherThemes[0]?.id ?? "");
  const [draftTaskIds, setDraftTaskIds] = useState<string[]>([]);
  const [draftVariants, setDraftVariants] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const selectedStudent = useMemo(
    () => students.find((student) => student.id === studentId),
    [students, studentId],
  );
  const studentTrack = selectedStudent?.track ?? "ege";
  const variants = variantsByTrack[studentTrack];
  const typeNumbers = typeNumbersForTrack(studentTrack);
  const selectedTheme = useMemo(
    () => teacherThemes.find((theme) => theme.id === draftThemeId),
    [teacherThemes, draftThemeId],
  );

  useEffect(() => {
    if (topics.length > 0 && !topics.includes(draftTopic)) {
      setDraftTopic(topics[0]);
    }
  }, [topics, draftTopic]);

  useEffect(() => {
    if (variants.length > 0 && !variants.includes(draftVariant)) {
      setDraftVariant(variants[0]);
    } else if (variants.length === 0) {
      setDraftVariant("");
    }
  }, [variants, draftVariant]);

  useEffect(() => {
    if (teacherThemes.length > 0 && !teacherThemes.some((t) => t.id === draftThemeId)) {
      setDraftThemeId(teacherThemes[0].id);
    } else if (teacherThemes.length === 0) {
      setDraftThemeId("");
    }
    setDraftTaskIds([]);
  }, [teacherThemes, draftThemeId]);

  useEffect(() => {
    setDraftVariants([]);
  }, [studentTrack]);

  function toggleDraftType(type: number) {
    setDraftTypes((current) =>
      current.includes(type)
        ? current.filter((value) => value !== type)
        : [...current, type].sort((a, b) => a - b),
    );
  }

  function toggleDraftVariant(variant: string) {
    setDraftVariants((current) =>
      current.includes(variant)
        ? current.filter((value) => value !== variant)
        : [...current, variant].sort(),
    );
  }

  function toggleDraftTask(taskId: string) {
    setDraftTaskIds((current) =>
      current.includes(taskId)
        ? current.filter((value) => value !== taskId)
        : [...current, taskId],
    );
  }

  function buildDraftItem(): HomeworkItem | null {
    if (draftKind === "lecture") {
      if (!draftTopic) {
        return null;
      }
      return { kind: "lecture", topic: draftTopic };
    }
    if (draftKind === "custom_theme") {
      if (!draftThemeId) {
        return null;
      }
      const item: HomeworkItem = {
        kind: "custom_theme",
        theme_id: draftThemeId,
      };
      if (draftTaskIds.length > 0) {
        item.task_ids = draftTaskIds;
      }
      return item;
    }
    if (draftKind === "test_by_type") {
      if (draftTypes.length === 0) {
        return null;
      }
      const item: HomeworkItem = { kind: "test_by_type", types: draftTypes };
      if (draftVariants.length > 0) {
        item.variants = draftVariants;
      }
      return item;
    }
    if (!draftVariant) {
      return null;
    }
    if (draftKind === "test_variant") {
      return { kind: "test_variant", variant: draftVariant };
    }
    if (draftTypes.length === 0) {
      return null;
    }
    return { kind: "test_partial", variant: draftVariant, types: draftTypes };
  }

  function itemDisplayLabel(item: HomeworkItem): string {
    if (item.kind === "custom_theme") {
      const theme = teacherThemes.find((row) => row.id === item.theme_id);
      const title = theme?.title ?? "Тема преподавателя";
      if (item.task_ids && item.task_ids.length > 0) {
        return `Тема: ${title} (${item.task_ids.length} зад.)`;
      }
      return `Тема: ${title}`;
    }
    return formatHomeworkItemLabel(item);
  }

  function renderTypeGrid() {
    const variantCount =
      draftVariants.length > 0 ? draftVariants.length : variants.length;
    return (
      <div className="flex flex-col gap-2">
        <span className="text-sm font-medium text-zinc-700">
          Номера заданий (type)
        </span>
        <div className="flex flex-wrap gap-2">
          {typeNumbers.map((type) => {
            const selected = draftTypes.includes(type);
            return (
              <button
                key={type}
                type="button"
                aria-pressed={selected ? "true" : "false"}
                onClick={() => toggleDraftType(type)}
                className={`min-w-[2.25rem] rounded-md border px-2 py-1 text-sm transition ${
                  selected
                    ? "border-chem-royal bg-chem-royal/10 text-chem-royal"
                    : "border-zinc-300 bg-white text-zinc-700 hover:border-zinc-400"
                }`}
              >
                {type}
              </button>
            );
          })}
        </div>
        {draftKind === "test_by_type" && draftTypes.length > 0 ? (
          <p className="text-xs text-zinc-500">
            {studentTrack === "ege"
              ? `ЕГЭ: задание №${draftTypes.join(", ")} из ${draftVariants.length > 0 ? "выбранных" : "каждого"} варианта (≈${estimateTestByTypeSteps(draftTypes, studentTrack, variantCount)} шагов).`
              : `ОГЭ: варианты задания типа ${draftTypes.join(", ")} (≈${estimateTestByTypeSteps(draftTypes, studentTrack, variantCount)} шагов).`}
          </p>
        ) : null}
      </div>
    );
  }

  function renderVariantGrid() {
    if (variants.length === 0) {
      return null;
    }
    return (
      <div className="flex flex-col gap-2">
        <span className="text-sm font-medium text-zinc-700">
          Варианты (необязательно — пусто = все)
        </span>
        <div className="flex flex-wrap gap-2">
          {variants.map((variant) => {
            const selected = draftVariants.includes(variant);
            return (
              <button
                key={variant}
                type="button"
                aria-pressed={selected ? "true" : "false"}
                onClick={() => toggleDraftVariant(variant)}
                className={`rounded-md border px-2 py-1 text-sm transition ${
                  selected
                    ? "border-chem-royal bg-chem-royal/10 text-chem-royal"
                    : "border-zinc-300 bg-white text-zinc-700 hover:border-zinc-400"
                }`}
              >
                {variant.replace(/\.txt$/, "")}
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  function renderThemeTaskCheckboxes() {
    const tasks = selectedTheme?.tasks ?? [];
    if (tasks.length === 0) {
      return (
        <p className="text-sm text-zinc-500">В теме пока нет заданий.</p>
      );
    }
    return (
      <div className="flex flex-col gap-2">
        <span className="text-sm font-medium text-zinc-700">
          Задания (необязательно — пусто = все)
        </span>
        <ul className="flex flex-col gap-2">
          {tasks.map((task) => {
            const selected = draftTaskIds.includes(task.id);
            const label = task.title?.trim() || `Задание ${task.sort_order + 1}`;
            return (
              <li key={task.id}>
                <label className="flex cursor-pointer items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={selected}
                    onChange={() => toggleDraftTask(task.id)}
                    className="h-4 w-4 rounded border-zinc-300"
                  />
                  <span>
                    {label}
                    <span className="ml-1 text-zinc-500">
                      ({task.grading_mode === "self_check" ? "самопроверка" : "авто"})
                    </span>
                  </span>
                </label>
              </li>
            );
          })}
        </ul>
      </div>
    );
  }

  function handleAddItem() {
    setError(null);
    const item = buildDraftItem();
    if (!item) {
      if (draftKind === "lecture") {
        setError("Выберите тему лекции.");
      } else if (draftKind === "custom_theme") {
        setError("Выберите тему преподавателя.");
      } else if (draftKind === "test_by_type") {
        setError("Выберите хотя бы один номер задания.");
      } else if (!draftVariant) {
        setError("Выберите вариант теста.");
      } else {
        setError("Выберите хотя бы один номер задания.");
      }
      return;
    }
    setItems((current) => [...current, item]);
  }

  function handleRemoveItem(index: number) {
    setItems((current) => current.filter((_, itemIndex) => itemIndex !== index));
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!title.trim()) {
      setError("Укажите название задания.");
      return;
    }
    if (items.length === 0) {
      setError("Добавьте хотя бы один пункт в задание.");
      return;
    }

    setSubmitting(true);
    try {
      await createHomework({
        student_id: studentId,
        title,
        description: description || null,
        items,
      });
      router.push("/teacher/homework");
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message || "Не удалось создать задание.");
      } else {
        setError("Не удалось создать задание. Попробуйте позже.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (students.length === 0) {
    return (
      <p className="text-sm text-zinc-500">
        Сначала создайте ученика на странице «Ученики».
      </p>
    );
  }

  const canAddTestItem = variants.length > 0;
  const canAddLectureItem = topics.length > 0;
  const canAddCustomTheme = teacherThemes.length > 0;

  return (
    <form
      onSubmit={handleSubmit}
      className="chem-card flex flex-col gap-6 rounded-lg p-6"
      noValidate
    >
      <h2 className="text-lg font-semibold text-zinc-900">Новое домашнее задание</h2>

      <div className="flex flex-col gap-1">
        <label htmlFor="hw-student" className="text-sm font-medium text-zinc-700">
          Ученик
        </label>
        <select
          id="hw-student"
          value={studentId}
          onChange={(e) => setStudentId(e.target.value)}
          className="chem-input rounded-md border border-zinc-300 bg-white px-3 py-2"
        >
          {students.map((student) => (
            <option key={student.id} value={student.id}>
              {student.email} ({student.track.toUpperCase()})
            </option>
          ))}
        </select>
        <p className="text-xs text-zinc-500">
          Трек {studentTrack.toUpperCase()}: доступны только варианты этого экзамена.
        </p>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="hw-title" className="text-sm font-medium text-zinc-700">
          Название
        </label>
        <input
          id="hw-title"
          required
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="chem-input rounded-md border border-zinc-300 bg-white px-3 py-2"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="hw-description" className="text-sm font-medium text-zinc-700">
          Описание (необязательно)
        </label>
        <textarea
          id="hw-description"
          rows={2}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="chem-input rounded-md border border-zinc-300 bg-white px-3 py-2"
        />
      </div>

      <fieldset className="flex flex-col gap-4 rounded-lg border border-zinc-200 p-4">
        <legend className="px-1 text-sm font-medium text-zinc-700">
          Добавить пункт
        </legend>

        <div className="flex flex-col gap-1">
          <label htmlFor="hw-draft-kind" className="text-sm font-medium text-zinc-700">
            Тип пункта
          </label>
          <select
            id="hw-draft-kind"
            value={draftKind}
            onChange={(e) => setDraftKind(e.target.value as HomeworkKind)}
            className="chem-input rounded-md border border-zinc-300 bg-white px-3 py-2"
          >
            <option value="lecture">Лекция</option>
            <option value="test_variant">Тест: целый вариант</option>
            <option value="test_partial">Тест: выбранные номера</option>
            <option value="test_by_type">Тест: номер по всем вариантам</option>
            <option value="custom_theme">Тема преподавателя</option>
          </select>
        </div>

        {draftKind === "lecture" ? (
          <div className="flex flex-col gap-1">
            <label htmlFor="hw-draft-topic" className="text-sm font-medium text-zinc-700">
              Тема
            </label>
            {!canAddLectureItem ? (
              <p className="text-sm text-zinc-500">
                Нет доступных тем. Проверьте базу лекций на сервере.
              </p>
            ) : (
              <select
                id="hw-draft-topic"
                value={draftTopic}
                onChange={(e) => setDraftTopic(e.target.value)}
                className="chem-input rounded-md border border-zinc-300 bg-white px-3 py-2"
              >
                {topics.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            )}
          </div>
        ) : draftKind === "custom_theme" ? (
          <>
            <div className="flex flex-col gap-1">
              <label
                htmlFor="hw-draft-teacher-theme"
                className="text-sm font-medium text-zinc-700"
              >
                Тема преподавателя
              </label>
              {!canAddCustomTheme ? (
                <p className="text-sm text-zinc-500">
                  Сначала создайте тему на странице «Темы».
                </p>
              ) : (
                <select
                  id="hw-draft-teacher-theme"
                  value={draftThemeId}
                  onChange={(e) => {
                    setDraftThemeId(e.target.value);
                    setDraftTaskIds([]);
                  }}
                  className="chem-input rounded-md border border-zinc-300 bg-white px-3 py-2"
                >
                  {teacherThemes.map((theme) => (
                    <option key={theme.id} value={theme.id}>
                      {theme.title} ({theme.tasks.length} зад.)
                    </option>
                  ))}
                </select>
              )}
            </div>
            {canAddCustomTheme ? renderThemeTaskCheckboxes() : null}
          </>
        ) : draftKind === "test_by_type" ? (
          <>
            <p className="text-sm text-zinc-600">
              Для ЕГЭ — одно задание выбранного номера из каждого варианта. Для
              ОГЭ — все варианты задания этого типа.
            </p>
            {renderTypeGrid()}
            {renderVariantGrid()}
          </>
        ) : (
          <>
            <div className="flex flex-col gap-1">
              <label
                htmlFor="hw-draft-variant"
                className="text-sm font-medium text-zinc-700"
              >
                Вариант
              </label>
              {!canAddTestItem ? (
                <p className="text-sm text-zinc-500">
                  Нет вариантов для трека {studentTrack.toUpperCase()}.
                </p>
              ) : (
                <select
                  id="hw-draft-variant"
                  value={draftVariant}
                  onChange={(e) => setDraftVariant(e.target.value)}
                  className="chem-input rounded-md border border-zinc-300 bg-white px-3 py-2"
                >
                  {variants.map((value) => (
                    <option key={value} value={value}>
                      {value.replace(/\.txt$/, "")}
                    </option>
                  ))}
                </select>
              )}
            </div>
            {draftKind === "test_partial" ? renderTypeGrid() : null}
          </>
        )}

        <button
          type="button"
          onClick={handleAddItem}
          disabled={
            draftKind === "lecture"
              ? !canAddLectureItem
              : draftKind === "custom_theme"
                ? !canAddCustomTheme
                : draftKind === "test_by_type"
                  ? false
                  : !canAddTestItem
          }
          className="inline-flex w-fit rounded-md border border-chem-royal px-4 py-2 text-sm font-medium text-chem-royal transition hover:bg-chem-royal/5 disabled:opacity-60"
        >
          Добавить пункт
        </button>
      </fieldset>

      <section className="flex flex-col gap-2">
        <h3 className="text-sm font-medium text-zinc-700">
          Состав задания ({items.length})
        </h3>
        {items.length === 0 ? (
          <p className="text-sm text-zinc-500">
            Пока нет пунктов. Добавьте лекции и/или тесты из разных вариантов.
          </p>
        ) : (
          <ol className="divide-y divide-zinc-200 rounded-lg border border-zinc-200">
            {items.map((item, index) => (
              <li
                key={`${item.kind}-${index}`}
                className="flex items-center justify-between gap-3 px-3 py-2 text-sm"
              >
                <span>
                  {index + 1}. {itemDisplayLabel(item)}
                </span>
                <button
                  type="button"
                  onClick={() => handleRemoveItem(index)}
                  className="text-xs text-[var(--chem-crimson)] hover:underline"
                >
                  Удалить
                </button>
              </li>
            ))}
          </ol>
        )}
      </section>

      {error ? (
        <p role="alert" className="text-sm text-[var(--chem-crimson)]">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={submitting || items.length === 0}
        className="chem-btn-primary px-4 py-2 disabled:opacity-60"
      >
        {submitting ? "Создание…" : "Назначить"}
      </button>
    </form>
  );
}
