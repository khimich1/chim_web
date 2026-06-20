"use client";

import { useState } from "react";

import { ContentBlocksEditor } from "@/components/teacher/ContentBlocksEditor";
import { ApiError } from "@/lib/api/client";
import {
  createThemeTask,
  deleteThemeTask,
  updateThemeTask,
} from "@/lib/api/teacher-themes";
import type { ContentBlock, CustomTask, GradingMode } from "@/lib/api/types";

function emptyBlocks(): ContentBlock[] {
  return [{ type: "text", content: "" }];
}

export function TaskEditor({
  themeId,
  task,
  onSaved,
  onCancel,
}: {
  themeId: string;
  task?: CustomTask;
  onSaved: (task: CustomTask) => void;
  onCancel?: () => void;
}) {
  const [title, setTitle] = useState(task?.title ?? "");
  const [gradingMode, setGradingMode] = useState<GradingMode>(
    task?.grading_mode ?? "auto",
  );
  const [questionBlocks, setQuestionBlocks] = useState<ContentBlock[]>(
    task?.question_blocks?.length ? task.question_blocks : emptyBlocks(),
  );
  const [correctValue, setCorrectValue] = useState(task?.correct_value ?? "");
  const [referenceBlocks, setReferenceBlocks] = useState<ContentBlock[]>(
    task?.reference_answer?.length ? task.reference_answer : emptyBlocks(),
  );
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function validateBlocks(blocks: ContentBlock[]): ContentBlock[] {
    return blocks.filter(
      (block) =>
        (block.type === "text" && block.content?.trim()) ||
        (block.type === "image" && block.url),
    );
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    const validQuestion = validateBlocks(questionBlocks);
    if (validQuestion.length === 0) {
      setError("Добавьте хотя бы один блок вопроса.");
      return;
    }
    if (gradingMode === "auto" && !correctValue.trim()) {
      setError("Укажите правильный ответ для автопроверки.");
      return;
    }
    const validReference =
      gradingMode === "self_check" ? validateBlocks(referenceBlocks) : null;
    if (gradingMode === "self_check" && (!validReference || validReference.length === 0)) {
      setError("Добавьте эталонный ответ для самопроверки.");
      return;
    }

    setSaving(true);
    try {
      const payload = {
        title: title.trim() || null,
        grading_mode: gradingMode,
        question_blocks: validQuestion,
        correct_value: gradingMode === "auto" ? correctValue.trim() : null,
        reference_answer: gradingMode === "self_check" ? validReference : null,
      };

      const saved = task
        ? await updateThemeTask(task.id, payload)
        : await createThemeTask(themeId, payload);
      onSaved(saved);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Не удалось сохранить задание.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!task) {
      return;
    }
    if (!window.confirm("Удалить задание?")) {
      return;
    }
    setDeleting(true);
    setError(null);
    try {
      await deleteThemeTask(task.id);
      onSaved({ ...task, id: "" });
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Не удалось удалить задание.",
      );
      setDeleting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="chem-card flex flex-col gap-4 rounded-lg p-4">
      <h3 className="text-base font-semibold text-zinc-900">
        {task ? "Редактировать задание" : "Новое задание"}
      </h3>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="task-title" className="text-sm font-medium text-zinc-700">
          Название (необязательно)
        </label>
        <input
          id="task-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="chem-input rounded-md border border-zinc-300 px-3 py-2 text-sm"
        />
      </div>

      <fieldset className="flex flex-col gap-2">
        <legend className="text-sm font-medium text-zinc-700">Режим проверки</legend>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="radio"
            name="grading-mode"
            checked={gradingMode === "auto"}
            onChange={() => setGradingMode("auto")}
          />
          Автопроверка (точный ответ)
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="radio"
            name="grading-mode"
            checked={gradingMode === "self_check"}
            onChange={() => setGradingMode("self_check")}
          />
          Самопроверка (сравнение с эталоном)
        </label>
      </fieldset>

      <ContentBlocksEditor
        label="Вопрос"
        blocks={questionBlocks}
        onChange={setQuestionBlocks}
      />

      {gradingMode === "auto" ? (
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="correct-value"
            className="text-sm font-medium text-zinc-700"
          >
            Правильный ответ
          </label>
          <input
            id="correct-value"
            type="text"
            value={correctValue}
            onChange={(e) => setCorrectValue(e.target.value)}
            className="chem-input rounded-md border border-zinc-300 px-3 py-2 text-sm"
          />
        </div>
      ) : (
        <ContentBlocksEditor
          label="Эталонный ответ"
          blocks={referenceBlocks}
          onChange={setReferenceBlocks}
        />
      )}

      {error ? (
        <p role="alert" className="text-sm text-[var(--chem-crimson)]">
          {error}
        </p>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <button
          type="submit"
          disabled={saving || deleting}
          className="chem-btn-primary px-4 py-2 text-sm disabled:opacity-60"
        >
          {saving ? "Сохранение…" : "Сохранить задание"}
        </button>
        {onCancel ? (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border border-zinc-300 px-4 py-2 text-sm text-zinc-700"
          >
            Отмена
          </button>
        ) : null}
        {task ? (
          <button
            type="button"
            onClick={() => void handleDelete()}
            disabled={saving || deleting}
            className="ml-auto text-sm text-[var(--chem-crimson)] hover:underline disabled:opacity-60"
          >
            {deleting ? "Удаление…" : "Удалить"}
          </button>
        ) : null}
      </div>
    </form>
  );
}
