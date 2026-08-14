"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useState } from "react";

import { ApiError, formatFetchError } from "@/lib/api/client";
import { submitLead, type LeadPayload } from "@/lib/api/leads";

const TG_URL = "https://t.me/himich_teacher";
const VK_URL = "https://vk.ru/himich_teachr24";

const CLASS_OPTIONS = [
  { value: "8", label: "8 класс" },
  { value: "9", label: "9 класс" },
  { value: "10", label: "10 класс" },
  { value: "11", label: "11 класс" },
] as const;

const GOAL_OPTIONS = [
  { value: "ege", label: "ЕГЭ" },
  { value: "oge", label: "ОГЭ" },
  { value: "school", label: "Школа" },
] as const;

type FormState = "idle" | "submitting" | "success" | "error";

interface LeadFormProps {
  sourcePage: string;
  formId?: string;
  showSocialLinks?: boolean;
}

export function LeadForm({
  sourcePage,
  formId = "lead-form",
  showSocialLinks = true,
}: LeadFormProps) {
  const searchParams = useSearchParams();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [schoolClass, setSchoolClass] = useState<LeadPayload["school_class"]>("11");
  const [goal, setGoal] = useState<LeadPayload["goal"]>("ege");
  const [comment, setComment] = useState("");
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [formState, setFormState] = useState<FormState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const utmSource = searchParams.get("utm_source") ?? undefined;
  const utmMedium = searchParams.get("utm_medium") ?? undefined;
  const utmCampaign = searchParams.get("utm_campaign") ?? undefined;

  const canSubmit = privacyAccepted && formState !== "submitting";

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!privacyAccepted) return;

    setErrorMessage(null);
    setFormState("submitting");

    try {
      await submitLead({
        name: name.trim(),
        phone: phone.trim(),
        school_class: schoolClass,
        goal,
        comment: comment.trim() || undefined,
        source_page: sourcePage,
        utm_source: utmSource,
        utm_medium: utmMedium,
        utm_campaign: utmCampaign,
      });
      setFormState("success");
    } catch (err) {
      setFormState("error");
      if (err instanceof ApiError && err.status === 429) {
        setErrorMessage("Слишком много попыток. Попробуйте через минуту.");
      } else {
        setErrorMessage(
          formatFetchError(err, "Не удалось отправить заявку. Попробуйте позже."),
        );
      }
    }
  }

  if (formState === "success") {
    return (
      <div
        className="chem-card rounded-xl p-6 text-center"
        role="status"
        aria-live="polite"
      >
        <p className="text-lg font-semibold text-chem-teal-dark">
          Спасибо! Перезвоним в течение 2 часов
        </p>
        <p className="mt-2 text-sm text-zinc-600">
          Или напишите в{" "}
          <a
            href={TG_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-chem-teal underline"
          >
            Telegram
          </a>
        </p>
      </div>
    );
  }

  return (
    <div className="chem-card rounded-xl p-5 sm:p-6">
      <form id={formId} onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
        <div className="flex flex-col gap-1">
          <label htmlFor={`${formId}-name`} className="text-sm font-medium text-zinc-700">
            Имя родителя или ученика
          </label>
          <input
            id={`${formId}-name`}
            name="name"
            type="text"
            required
            autoComplete="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="rounded-md border border-zinc-300 px-3 py-2 text-base text-zinc-900"
          />
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor={`${formId}-phone`} className="text-sm font-medium text-zinc-700">
            Телефон
          </label>
          <input
            id={`${formId}-phone`}
            name="phone"
            type="tel"
            required
            autoComplete="tel"
            placeholder="+7 (900) 123-45-67"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className="rounded-md border border-zinc-300 px-3 py-2 text-base text-zinc-900"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="flex flex-col gap-1">
            <label htmlFor={`${formId}-class`} className="text-sm font-medium text-zinc-700">
              Класс
            </label>
            <select
              id={`${formId}-class`}
              name="school_class"
              required
              value={schoolClass}
              onChange={(e) =>
                setSchoolClass(e.target.value as LeadPayload["school_class"])
              }
              className="rounded-md border border-zinc-300 px-3 py-2 text-base text-zinc-900"
            >
              {CLASS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <label htmlFor={`${formId}-goal`} className="text-sm font-medium text-zinc-700">
              Цель
            </label>
            <select
              id={`${formId}-goal`}
              name="goal"
              required
              value={goal}
              onChange={(e) => setGoal(e.target.value as LeadPayload["goal"])}
              className="rounded-md border border-zinc-300 px-3 py-2 text-base text-zinc-900"
            >
              {GOAL_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <label htmlFor={`${formId}-comment`} className="text-sm font-medium text-zinc-700">
            Комментарий <span className="font-normal text-zinc-500">(необязательно)</span>
          </label>
          <textarea
            id={`${formId}-comment`}
            name="comment"
            rows={2}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className="rounded-md border border-zinc-300 px-3 py-2 text-base text-zinc-900"
          />
        </div>

        <label className="flex items-start gap-2 text-sm text-zinc-700">
          <input
            type="checkbox"
            checked={privacyAccepted}
            onChange={(e) => setPrivacyAccepted(e.target.checked)}
            className="mt-0.5 h-4 w-4 rounded border-zinc-300 text-chem-teal"
            required
          />
          <span>
            Согласен на{" "}
            <Link href="/privacy" className="text-chem-teal underline">
              обработку персональных данных
            </Link>
          </span>
        </label>

        {errorMessage ? (
          <p role="alert" className="text-sm text-text-negative">
            {errorMessage}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={!canSubmit}
          className="chem-btn-primary w-full px-4 py-3 text-base font-medium"
        >
          {formState === "submitting" ? "Отправляем…" : "Записаться на диагностику"}
        </button>

        <p className="text-center text-xs text-zinc-500">
          Без обязательств · ответим в течение 2 часов
        </p>
      </form>

      {showSocialLinks ? (
        <div className="mt-4 flex flex-col gap-2 border-t border-zinc-100 pt-4 text-center text-sm text-zinc-600">
          <p>
            Или напишите в{" "}
            <a
              href={TG_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-chem-teal underline"
            >
              Telegram
            </a>
          </p>
          <p>
            <a
              href={VK_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="font-medium text-chem-teal underline"
            >
              ВКонтакте
            </a>
          </p>
        </div>
      ) : null}
    </div>
  );
}
