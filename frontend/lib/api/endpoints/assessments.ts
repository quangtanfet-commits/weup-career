"use client";

import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

/**
 * Assessment endpoints (architecture.md §6.2, group `assessments`; FR-10..15,
 * CP-3). All run on the client with the in-memory bearer token — assessment
 * results are sensitive (`is_sensitive=true`) and must never be fetched in a
 * Server Component (no RSC cache leak). Request/response shapes come from the
 * generated OpenAPI schema so the FE↔BE contract is compile-time checked (NFR-20).
 */
export type InstrumentOut = components["schemas"]["InstrumentOut"];
export type InstrumentType = components["schemas"]["InstrumentType"];
export type SubmitRequest = components["schemas"]["SubmitRequest"];
export type ResultMetaOut = components["schemas"]["ResultMetaOut"];
export type ResultDetailOut = components["schemas"]["ResultDetailOut"];

/** GET /assessments — list the active instruments (RIASEC / VIPS / MBTI). */
export async function listInstruments(): Promise<InstrumentOut[]> {
  return apiFetch<InstrumentOut[]>("/assessments");
}

/**
 * POST /assessments/{instrument_type}/submit — submit answers, creating a new
 * versioned `AssessmentResult` (FR-11/FR-15). Returns metadata only (the
 * decrypted payload is read separately via an audited GET, CP-3).
 */
export async function submitAssessment(
  instrumentType: InstrumentType,
  body: SubmitRequest,
): Promise<ResultMetaOut> {
  return apiFetch<ResultMetaOut>(
    `/assessments/${encodeURIComponent(instrumentType)}/submit`,
    { method: "POST", body },
  );
}

/**
 * GET /me/assessments/{result_id} — read a single result with its decrypted
 * payload. Every read is an audited sensitive access (CP-3); callers MUST treat
 * this as no-cache (see `useSensitiveQuery`) so a re-read is a fresh audited GET
 * rather than a cache hit.
 */
export async function getResult(resultId: string): Promise<ResultDetailOut> {
  return apiFetch<ResultDetailOut>(
    `/me/assessments/${encodeURIComponent(resultId)}`,
  );
}

/**
 * DELETE /me/assessments/{result_id} — erase a result (data-subject right,
 * FR-14). Deliberately NOT behind the consent gate so a child who has revoked
 * consent can still delete their own data (architecture.md §6.2 note c).
 */
export async function deleteResult(resultId: string): Promise<void> {
  await apiFetch<void>(`/me/assessments/${encodeURIComponent(resultId)}`, {
    method: "DELETE",
  });
}
