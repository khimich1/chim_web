import { describe, expect, it } from "vitest";

import type { HomeworkAssignment } from "@/lib/api/types";
import {
  formatWaveSummary,
  groupHomeworkWaves,
} from "@/lib/students/groupHomeworkWaves";

function row(
  overrides: Partial<HomeworkAssignment> & Pick<HomeworkAssignment, "id" | "student_id">,
): HomeworkAssignment {
  return {
    student_email: null,
    title: "Алканы",
    description: null,
    due_at: null,
    items: [],
    status: "assigned",
    created_at: "2026-06-20T10:00:00Z",
    template_id: "t1",
    source_group_id: "g1",
    assign_batch_id: "batch-1",
    cancelled_at: null,
    submission: null,
    progress: [],
    active_test_session_id: null,
    ...overrides,
  };
}

describe("groupHomeworkWaves", () => {
  it("groups by assign_batch_id for the group and skips null batches", () => {
    const waves = groupHomeworkWaves(
      [
        row({ id: "h1", student_id: "s1" }),
        row({ id: "h2", student_id: "s2" }),
        row({
          id: "h3",
          student_id: "s3",
          assign_batch_id: null,
          source_group_id: "g1",
        }),
        row({
          id: "h4",
          student_id: "s4",
          source_group_id: "other",
          assign_batch_id: "batch-other",
        }),
      ],
      "g1",
    );

    expect(waves).toHaveLength(1);
    expect(waves[0].assignBatchId).toBe("batch-1");
    expect(waves[0].total).toBe(2);
    expect(waves[0].anchorId).toBe("h1");
    expect(formatWaveSummary(waves[0])).toContain("2 уч.");
  });

  it("marks cancelled waves", () => {
    const waves = groupHomeworkWaves(
      [
        row({ id: "h1", student_id: "s1", status: "cancelled" }),
        row({ id: "h2", student_id: "s2", status: "cancelled" }),
      ],
      "g1",
    );
    expect(waves[0].allCancelled).toBe(true);
    expect(waves[0].canCancel).toBe(false);
  });
});
