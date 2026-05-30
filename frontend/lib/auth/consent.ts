import type { SessionUser } from "@/lib/auth/store";

/**
 * Consent-gate predicate (architecture.md §0, §5.3, §7 CP-1). A child under 16
 * whose account is not yet `active` has no active `GuardianConsent`, so every
 * `[gate]` feature (assessments submit, progress, recommendations, wellbeing)
 * must be soft-blocked in the UI with a CTA to `/consent`. The backend remains
 * the final enforcement layer (403 `GUARDIAN_CONSENT_REQUIRED`); the UI only
 * avoids leading the user into a dead end.
 *
 * Note: `pending_guardian_consent` is the canonical pre-consent status, but we
 * gate on "not active" so a `suspended`/other non-active state is also blocked
 * rather than silently allowed.
 */
export function isConsentGated(user: SessionUser | null): boolean {
  if (!user) return false;
  return user.age_band === "under_16" && user.account_status !== "active";
}
