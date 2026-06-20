"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { login } from "@/lib/api/auth";
import { ApiError, formatFetchError } from "@/lib/api/client";

interface LoginFormProps {
  redirectTo?: string | null;
}

export function LoginForm({ redirectTo = null }: LoginFormProps) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const user = await login(email, password);
      if (redirectTo) {
        router.replace(redirectTo);
      } else {
        router.replace(user.role === "teacher" ? "/teacher" : "/student");
      }
      router.refresh();
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("Неверный email или пароль");
      } else {
        setError(formatFetchError(err, "Не удалось войти. Попробуйте позже."));
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      <div className="flex flex-col gap-1">
        <label htmlFor="email" className="text-sm font-medium text-zinc-700">
          Email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="username"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="chem-input min-h-[44px] w-full rounded-md border border-zinc-300 px-3 py-2 text-zinc-900"
        />
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="password" className="text-sm font-medium text-zinc-700">
          Пароль
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="chem-input min-h-[44px] w-full rounded-md border border-zinc-300 px-3 py-2 text-zinc-900"
        />
      </div>

      <div aria-live="polite">
        {error ? (
          <p role="alert" className="text-sm text-[var(--chem-crimson)]">
            {error}
          </p>
        ) : null}
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="chem-btn-primary mt-2 min-h-[44px] px-4 py-2.5 disabled:opacity-60"
      >
        {submitting ? "Вход…" : "Войти"}
      </button>
    </form>
  );
}
