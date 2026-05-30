import { describe, it, expect } from "vitest";

import { isConsentGated } from "@/lib/auth/consent";
import type { SessionUser } from "@/lib/auth/store";

function makeUser(over: Partial<SessionUser>): SessionUser {
  return { id: "u1", email: "a@b.vn", roles: ["student"], ...over };
}

describe("isConsentGated", () => {
  it("gates a child <16 whose account is not active", () => {
    expect(
      isConsentGated(
        makeUser({
          age_band: "under_16",
          account_status: "pending_guardian_consent",
        }),
      ),
    ).toBe(true);
  });

  it("gates a child <16 in any non-active state (e.g. suspended)", () => {
    expect(
      isConsentGated(
        makeUser({ age_band: "under_16", account_status: "suspended" }),
      ),
    ).toBe(true);
  });

  it("does NOT gate a child <16 once the account is active", () => {
    expect(
      isConsentGated(
        makeUser({ age_band: "under_16", account_status: "active" }),
      ),
    ).toBe(false);
  });

  it("does NOT gate users aged 16+ regardless of status", () => {
    expect(
      isConsentGated(
        makeUser({ age_band: "16_17", account_status: "pending_guardian_consent" }),
      ),
    ).toBe(false);
    expect(
      isConsentGated(makeUser({ age_band: "adult", account_status: "active" })),
    ).toBe(false);
  });

  it("does NOT gate an anonymous (null) user — public content is never wrapped", () => {
    expect(isConsentGated(null)).toBe(false);
  });
});
