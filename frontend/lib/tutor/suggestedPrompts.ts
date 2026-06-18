import type { TutorPageContext } from "@/lib/api/tutor";

export interface SuggestedPrompt {
  label: string;
  message: string;
}

/** Contextual starter prompts (tutor-rag §16.3 U3). */
export function getSuggestedPrompts(
  context: TutorPageContext,
): SuggestedPrompt[] {
  if (context.test_session_id) {
    return [
      {
        label: "Подскажи теорию",
        message:
          "Подскажи теорию из учебника, которая поможет решить это задание.",
      },
      {
        label: "Объясни кратко",
        message:
          "Объясни кратко ключевые понятия для этого типа заданий.",
      },
    ];
  }

  if (context.topic) {
    return [
      {
        label: "Объясни кратко",
        message: `Объясни кратко тему «${context.topic}».`,
      },
      {
        label: "Проверь меня",
        message: `Проверь меня по теме «${context.topic}» — задай вопросы для самопроверки.`,
      },
    ];
  }

  if (context.homework_id) {
    return [
      {
        label: "Что задано?",
        message: "Что мне задано по домашней работе?",
      },
    ];
  }

  return [
    {
      label: "Помоги с теорией",
      message: "Помоги разобраться с темой из учебника.",
    },
  ];
}
