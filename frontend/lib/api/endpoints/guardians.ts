"use client";

import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

/**
 * Guardian-link / [CRED_69E0AC5C] endpoints (architecture.md §6.2, group `guardians`;
 * CP-1/CP-2). Request/response shapes come from the generated OpenAPI schema so
 * the FE↔BE contract is compile-time checked (NFR-20). All run on the client
 * with the in-memory bearer token.
 */
export type InviteRequest = components["schemas"]["InviteRequest"];
export type GuardianLinkOut = components["schemas"]["GuardianLinkOut"];
export type ConsentRequest = components["schemas"]["ConsentRequest"];
export type RevokeRequest = components["schemas"]["RevokeRequest"];
export type ConsentOut = components["schemas"]["ConsentOut"];

/** POST /guardians/invite — a child <16 invites a guardian by email (FR-03). */
export async function inviteGuardian(
  payload: InviteRequest,
): Promise<GuardianLinkOut> {
  return apiFetch<GuardianLinkOut>("/guardians/invite", {
    method: "POST",
    body: payload,
  });
}

/** POST /guardians/consent — a guardian grants consent against a verified link. */
export async function grantConsent(
  payload: ConsentRequest,
): Promise<ConsentOut> {
  return apiFetch<ConsentOut>("/guardians/consent", {
    method: "POST",
    body: payload,
  });
}

/** POST /guardians/consent/revoke — a guardian revokes consent (CP-2). */
export async function revokeConsent(
  payload: RevokeRequest,
): Promise<ConsentOut> {
  return apiFetch<ConsentOut>("/guardians/consent/revoke", {
    method: "POST",
    body: payload,
  });
}
