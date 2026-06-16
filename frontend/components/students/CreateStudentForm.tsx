"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { createStudent } from "@/lib/api/students";
import { ApiError } from "@/lib/api/client";
import type { Track } from "@/lib/api/types";

export function CreateStudentForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [track, setTrack] = useState<Track>("ege");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createStudent({ email, password, track });
      setEmail("");
      setPassword("");
      setTrack("ege");
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 403) {
          setError("Недостаточно прав для создания ученика.");
        } else if (err.status === 409) {
          setError("Этот email уже зарегистрирован.");
        } else if (err.status === 422) {
          setError("Проверьте email, пароль (мин. 6 символов) и трек.");
        } else {
          setError(err.message || "Не удалось создать ученика.");
        }
      } else {
        setError("Не удалось создать ученика. Попробуйте позже.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="chem-card flex flex-col gap-4 rounded-lg p-6"
      noValidate
    >
      <h2 className="text-lg font-semibold text-zinc-900">Новый ученик</h2>

      <div className="flex flex-col gap-1">
        <label htmlFor="student-email" className="text-sm font-medium text-zinc-700">
          Email
        </label>
        <input
          id="student-email"
          name="email"
          type="email"
          autoComplete="off"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="chem-input rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label
          htmlFor="student-password"
          className="text-sm font-medium text-zinc-700"
        >
          Временный пароль
        </label>
        <input
          id="student-password"
          name="password"
          type="password"
          autoComplete="new-password"
          required
          minLength={6}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="chem-input rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="student-track" className="text-sm font-medium text-zinc-700">
          Трек
        </label>
        <select
          id="student-track"
          name="track"
          value={track}
          onChange={(e) => setTrack(e.target.value as Track)}
          className="chem-input rounded-md border border-zinc-300 bg-white px-3 py-2 text-zinc-900"
        >
          <option value="ege">ЕГЭ</option>
          <option value="oge">ОГЭ</option>
        </select>
      </div>

      {error ? (
        <p role="alert" className="text-sm text-[var(--chem-crimson)]">
          {error}
        </p>
      ) : null}

      <button
        type="submit"
        disabled={submitting}
        className="chem-btn-primary px-4 py-2 disabled:opacity-60"
      >
        {submitting ? "Создание…" : "Создать ученика"}
      </button>
    </form>
  );
}
