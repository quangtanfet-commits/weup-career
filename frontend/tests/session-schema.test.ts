import { describe, it, expect } from "vitest";

import {
  counselingSessionSchema,
  toCreateSessionPayload,
  NOTES_MAX_LENGTH,
} from "@/features/counseling/session.schema";

/**
 * Counseling-session schema (FR-81). A session needs a student and a tier;
 * notes are optional free text, bounded in length.
 */
describe("counselingSessionSchema", () => {
  it("accepts a valid session and maps to the backend payload", () => {
    const parsed = counselingSessionSchema.parse({
      student_id: "stu-1",
      tier: "2",
      notes: "  Ghi chú  ",
    });
    expect(toCreateSessionPayload(parsed)).toEqual({
      student_id: "stu-1",
      tier: "2",
      notes: "Ghi chú",
    });
  });

  it("rejects a missing student id", () => {
    const result = counselingSessionSchema.safeParse({
      student_id: "  ",
      tier: "3",
      notes: "",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an out-of-range tier", () => {
    const result = counselingSessionSchema.safeParse({
      student_id: "stu-1",
      tier: "4",
      notes: "",
    });
    expect(result.success).toBe(false);
  });

  it("rejects notes longer than the max", () => {
    const result = counselingSessionSchema.safeParse({
      student_id: "stu-1",
      tier: "1",
      notes: "x".repeat(NOTES_MAX_LENGTH + 1),
    });
    expect(result.success).toBe(false);
  });
});
