/** Mirrors backend `resolve_public_display_name` for leaderboard row matching. */
export function resolvePublicDisplayName(
  displayName: string | null | undefined,
  studentId: string,
): string {
  if (displayName?.trim()) {
    return displayName.trim();
  }
  const hex = studentId.replace(/-/g, "");
  return `Ученик-${hex.slice(0, 8)}`;
}
