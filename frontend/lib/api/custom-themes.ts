import { apiFetch } from "@/lib/api/client";
import type { CustomThemeListItem } from "@/lib/api/types";

export function listCustomThemes(): Promise<CustomThemeListItem[]> {
  return apiFetch<CustomThemeListItem[]>("/api/custom-themes");
}
