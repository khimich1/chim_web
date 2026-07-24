/** Shared MIME allowlist and DataTransfer extractors for image intake. */

const ALLOWED_IMAGE_MIMES = new Set(["image/jpeg", "image/png", "image/webp"]);

/** Display classes matching CustomQuestionContent / QuestionContent. */
export const CONTENT_IMAGE_CLASS =
  "my-3 block h-auto max-w-full rounded-md border border-zinc-200 object-contain";

export const IMAGE_INTAKE_HINT =
  "Можно вставить изображение из буфера (Ctrl+V) или перетащить файл";

export function isAllowedImageMime(mime: string): boolean {
  return ALLOWED_IMAGE_MIMES.has(mime);
}

export function isAllowedImageFile(file: File): boolean {
  return isAllowedImageMime(file.type);
}

export type ImageFilesFromDataTransferResult = {
  files: File[];
  truncated: boolean;
};

/**
 * Extract allowed image files from clipboard or drag DataTransfer.
 * Preserves order; truncates to `limit` and sets `truncated` when extras exist.
 */
export function imageFilesFromDataTransfer(
  data: DataTransfer | null,
  options: { limit: number },
): ImageFilesFromDataTransferResult {
  if (!data || options.limit <= 0) {
    return { files: [], truncated: false };
  }

  const collected: File[] = [];

  if (data.items && data.items.length > 0) {
    for (const item of Array.from(data.items)) {
      if (item.kind !== "file") {
        continue;
      }
      const file = item.getAsFile();
      if (file && isAllowedImageFile(file)) {
        collected.push(file);
      }
    }
  } else if (data.files && data.files.length > 0) {
    for (const file of Array.from(data.files)) {
      if (isAllowedImageFile(file)) {
        collected.push(file);
      }
    }
  }

  const truncated = collected.length > options.limit;
  return {
    files: collected.slice(0, options.limit),
    truncated,
  };
}
