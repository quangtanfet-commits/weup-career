import { describe, it, expect } from "vitest";

import {
  supportRequestSchema,
  toSupportRequestPayload,
  MESSAGE_MAX_LENGTH,
} from "@/features/wellbeing/support-request.schema";

describe("supportRequestSchema", () => {
  it("rejects an empty / whitespace-only message", () => {
    expect(supportRequestSchema.safeParse({ message: "" }).success).toBe(false);
    expect(supportRequestSchema.safeParse({ message: "   " }).success).toBe(
      false,
    );
  });

  it("trims the message and accepts valid free text", () => {
    const parsed = supportRequestSchema.parse({
      message: "  Em muốn nói chuyện với chuyên viên tư vấn.  ",
    });
    expect(parsed.message).toBe("Em muốn nói chuyện với chuyên viên tư vấn.");
  });

  it("rejects a message longer than the max length", () => {
    const tooLong = "a".repeat(MESSAGE_MAX_LENGTH + 1);
    expect(supportRequestSchema.safeParse({ message: tooLong }).success).toBe(
      false,
    );
  });

  it("maps form values to the backend payload shape", () => {
    expect(toSupportRequestPayload({ message: "Xin chào" })).toEqual({
      message: "Xin chào",
    });
  });
});
