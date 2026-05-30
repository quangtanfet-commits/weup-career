"use client";

import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

/**
 * Wellbeing endpoints (architecture.md §6.2, group `wellbeing`; FR-70/FR-71,
 * NL4). A learner who shows signs of needing support can create a
 * `SupportRequest`, which the backend routes to a Tier-3 counselor. The records
 * are **routing-only**: they carry NO diagnosis/risk fields (NG-03) — the UI
 * never assesses or implies a medical evaluation, it only opens a safe path to
 * human help.
 *
 * Request/response shapes come from the generated OpenAPI schema so the FE↔BE
 * contract is compile-time checked (NFR-20). Both calls run on the client with
 * the in-memory bearer token and pass through the backend consent gate
 * (B+consent), so a soft consent gate is shown in the UI for children <16
 * without active guardian consent.
 */
export type SupportRequestCreate =
  components["schemas"]["SupportRequestCreate"];
export type SupportRequestOut = components["schemas"]["SupportRequestOut"];
export type SupportRequestStatus =
  components["schemas"]["SupportRequestStatus"];

/**
 * POST /wellbeing/support-request — create a support request that routes the
 * learner to a counselor (Tier 3) (FR-71). The body is plain free text; no
 * structured risk signals are collected.
 */
export async function createSupportRequest(
  payload: SupportRequestCreate,
): Promise<SupportRequestOut> {
  return apiFetch<SupportRequestOut>("/wellbeing/support-request", {
    method: "POST",
    body: payload,
  });
}

/** GET /wellbeing/support-requests — list the signed-in learner's own requests. */
export async function listSupportRequests(): Promise<SupportRequestOut[]> {
  return apiFetch<SupportRequestOut[]>("/wellbeing/support-requests");
}
