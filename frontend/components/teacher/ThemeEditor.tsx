"use client";

import { useState } from "react";

import { ApiError } from "@/lib/api/client";
import { updateTeacherTheme } from "@/lib/api/teacher-themes";
import type { TeacherTheme } from "@/lib/api/types";

export function ThemeEditor({
  theme,
  onSaved,
}: {
  theme: TeacherTheme;
  onSaved: (theme: TeacherTheme) => void;
}) {
  const [title, setTitle] = useState(theme.title);
  const [description, setDescription] = useState(theme.description ?? "");
  const [isPublished, setIsPublished] = useState(theme.is_published);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setSuccess(false);

    if (!title.trim()) {
      setError("Укажите название темы.");
      return;
    }

    setSaving(true);
    try {
      const updated = await updateTeacherTheme(theme.id, {
        title: title.trim(),
        description: description.trim() || null,
        is_published: isPublished,
      });
      onSaved(updated);
      setSuccess(true);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Не удалось сохранить тему.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="chem-card flex flex-col gap-4 rounded-lg p-4">
      <h2 className="text-lg font-semibold text-zinc-900">Параметры темы</h2>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="theme-title" className="text-sm font-medium text-zinc-700">
          Название
        </label>
        <input
          id="theme-title"
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="chem-input rounded-md border border-zinc-300 px-3 py-2 text-sm"
          required
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="theme-description"
          className="text-sm font-medium text-zinc-700"
        >
          Описание
        </label>
        <textarea
          id="theme-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="chem-input rounded-md border border-zinc-300 px-3 py-2 text-sm"
        />
      </div>

      <label className="flex items-center gap-2 text-sm text-zinc-700">
        <input
          type="checkbox"
          checked={isPublished}
          onChange={(e) => setIsPublished(e.target.checked)}
        />
        Опубликована (видна ученикам)
      </label>

      {error ? (
        <p role="alert" className="text-sm text-[var(--chem-crimson)]">
          {error}
        </p>
      ) : null}
      {success ? (
        <p role="status" className="text-sm text-chem-teal-dark">
          Сохранено
        </p>
      ) : null}

      <button
        type="submit"
        disabled={saving}
        className="chem-btn-primary self-start px-4 py-2 text-sm disabled:opacity-60"
      >
        {saving ? "Сохранение…" : "Сохранить тему"}
      </button>
    </form>
  );
}
