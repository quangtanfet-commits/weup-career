"use client";

import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

/**
 * Competency-tree & K-A-R progress endpoints (architecture.md §6.2, group
 * `competency`; FR-20..24, CP-8). These are personal/authed reads-and-writes,
 * so they run on the client with the in-memory bearer token via `apiFetch`
 * (architecture.md §5.4 — personal data never goes through RSC). The
 * request/response shapes come from the generated OpenAPI schema so the FE↔BE
 * contract stays compile-time checked (NFR-20).
 */
export type Competency = components["schemas"]["CompetencyOut"];
export type Indicator = components["schemas"]["IndicatorOut"];
export type ProgressItem = components["schemas"]["ProgressItemOut"];
export type CompetencyArea = components["schemas"]["CompetencyArea"];
export type Depth = components["schemas"]["Depth"];
export type DevPhase = components["schemas"]["DevPhase"];

export type DevPhaseOut = components["schemas"]["DevPhaseOut"];
export type SetDevPhaseRequest = components["schemas"]["SetDevPhaseRequest"];
export type RecordIndicatorOut = components["schemas"]["RecordIndicatorOut"];
export type RecordIndicatorRequest =
  components["schemas"]["RecordIndicatorRequest"];

/** GET /competencies — the fixed 12-competency tree with its indicators (FR-20/21). */
export async function listCompetencies(): Promise<Competency[]> {
  return apiFetch<Competency[]>("/competencies");
}

/**
 * GET /me/progress — the learner's current (competency, depth) coordinates and
 * the per-area dev_phase (FR-22/23). Consent-gated server-side (CP-1).
 */
export async function getMyProgress(): Promise<ProgressItem[]> {
  return apiFetch<ProgressItem[]>("/me/progress");
}

/**
 * POST /me/progress/dev-phase — record a (possibly deviating) dev_phase for one
 * area (FR-23). Students may deviate from the school_level-inferred default;
 * working users accumulate one phase per area. Consent-gated (CP-1/CP-2).
 */
export async function setDevPhase(
  payload: SetDevPhaseRequest,
): Promise<DevPhaseOut> {
  return apiFetch<DevPhaseOut>("/me/progress/dev-phase", {
    method: "POST",
    body: payload,
  });
}

/**
 * POST /me/progress/indicators — record an achieved indicator. The backend only
 * ever advances depth K→A→R and keeps history (CP-8); the response says whether
 * this write advanced the current depth. Consent-gated (CP-1/CP-2).
 */
export async function recordIndicator(
  payload: RecordIndicatorRequest,
): Promise<RecordIndicatorOut> {
  return apiFetch<RecordIndicatorOut>("/me/progress/indicators", {
    method: "POST",
    body: payload,
  });
}
