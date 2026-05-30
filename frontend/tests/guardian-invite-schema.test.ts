import { describe, it, expect } from "vitest";

import {
  guardianInviteSchema,
  toGuardianInvitePayload,
  relationships,
} from "@/features/consent/guardian-invite.schema";

describe("guardianInviteSchema", () => {
  it("accepts a valid guardian email + relationship and normalises the email", () => {
    const result = guardianInviteSchema.safeParse({
      guardian_email: "  Me@Example.VN ",
      relationship: "mother",
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.guardian_email).toBe("me@example.vn");
    }
  });

  it("rejects an empty email", () => {
    const result = guardianInviteSchema.safeParse({
      guardian_email: "",
      relationship: "mother",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid email", () => {
    const result = guardianInviteSchema.safeParse({
      guardian_email: "nope",
      relationship: "father",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an unknown relationship", () => {
    const result = guardianInviteSchema.safeParse({
      guardian_email: "me@example.vn",
      relationship: "sibling",
    });
    expect(result.success).toBe(false);
  });

  it("exposes the three supported relationships", () => {
    expect(relationships).toEqual(["mother", "father", "guardian"]);
  });
});

describe("toGuardianInvitePayload", () => {
  it("maps to the backend InviteRequest shape", () => {
    expect(
      toGuardianInvitePayload({
        guardian_email: "me@example.vn",
        relationship: "guardian",
      }),
    ).toEqual({ guardian_email: "me@example.vn", relationship: "guardian" });
  });
});
