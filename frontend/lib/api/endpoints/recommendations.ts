"use client";

import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

/**
 * Recommendation endpoints (architecture.md §6.2, group `reco`; FR-60..63,
 * CP-5/CP-6). The career-guidance engine produces a `Recommendation` that
 * ALWAYS carries an explainable `rationale` (CP-6) and ALWAYS waits for an
 * explicit human decision before it becomes effective (CP-5) — the system never
 * acts on a learner's behalf.
 *
 * Request/response shapes come from the generated OpenAPI schema so the FE↔BE
 * contract is compile-time checked (NFR-20). All three calls run on the client
 * with the in-memory bearer token via `apiFetch` (architecture.md §5.4 —
 * personal data never goes through the RSC layer). `POST /recommendations`
 * passes the backend consent gate (B+consent); read/confirm are authorised by
 * ownership/guardian/counselor relation (404 on no access — existence-hiding).
 */
export type RecommendationOut = components["schemas"]["RecommendationOut"];
export type ConfirmRequest = components["schemas"]["ConfirmRequest"];
export type RecoDecision = components["schemas"]["RecoDecision"];

/**
 * POST /recommendations — generate a recommendation for the signed-in learner
 * (FR-60). Consent-gated server-side (CP-1). The backend always returns a
 * `rationale` (CP-6) and `requires_human_confirmation=true` (CP-5); it never
 * applies the recommendation itself. Takes no request body.
 */
export async function generateRecommendation(): Promise<RecommendationOut> {
  return apiFetch<RecommendationOut>("/recommendations", { method: "POST" });
}

/**
 * GET /recommendations/{reco_id} — read a recommendation the caller is
 * authorised for (owner/guardian/counselor). A caller without a relation gets a
 * 404 (existence-hiding), surfaced as a neutral not-found state by the UI.
 */
export async function getRecommendation(
  recoId: string,
): Promise<RecommendationOut> {
  return apiFetch<RecommendationOut>(
    `/recommendations/${encodeURIComponent(recoId)}`,
  );
}

/**
 * POST /recommendations/{reco_id}/confirm — record the explicit human decision
 * (accepted/rejected/deferred) that makes the recommendation effective (CP-5).
 * Only ever called from an explicit user action; never auto-applied, never
 * optimistic. Returns the updated recommendation with `confirmed_by` /
 * `confirmed_decision` set.
 */
export async function confirmRecommendation(
  recoId: string,
  body: ConfirmRequest,
): Promise<RecommendationOut> {
  return apiFetch<RecommendationOut>(
    `/recommendations/${encodeURIComponent(recoId)}/confirm`,
    { method: "POST", body },
  );
}
