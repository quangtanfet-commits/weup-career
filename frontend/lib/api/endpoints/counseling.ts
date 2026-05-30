"use client";

import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

/**
 * Counselor / school-channel endpoints (architecture.md §6.2, group `school`;
 * FR-80..83, CP-3/CP-4). Every call is Bearer + role `counselor`, enforced by
 * the backend per request via DB-relational `SchoolMembership` (the school
 * channel is NOT a JWT claim — a counselor is only authorised within the school
 * they belong to, CP-4).
 *
 * CP-3 (de-sensitized): the counselor only ever reads de-sensitized shapes —
 * `RosterEntryOut` and `StudentProgressOut` carry instrument + derived
 * summary/competency codes, never the raw assessment payload. There is
 * deliberately no client-side endpoint that returns a learner's protected
 * answers here.
 *
 * Request/response shapes come from the generated OpenAPI schema so the FE↔BE
 * contract is compile-time checked (NFR-20); none are hand-rolled.
 */
export type RosterEntryOut = components["schemas"]["RosterEntryOut"];
export type StudentProgressOut = components["schemas"]["StudentProgressOut"];
export type CounselorProgressItemOut =
  components["schemas"]["CounselorProgressItemOut"];
export type DesensitizedAssessmentOut =
  components["schemas"]["DesensitizedAssessmentOut"];
export type CounselingSessionOut =
  components["schemas"]["CounselingSessionOut"];
export type CreateSessionRequest =
  components["schemas"]["CreateSessionRequest"];
export type CounselingTier = components["schemas"]["CounselingTier"];

/**
 * GET /school/{school_id}/students — the de-sensitized student roster for a
 * school the counselor is assigned to (FR-82, CP-3). A 403/404 from the backend
 * (not a member / not authorised) is surfaced as a neutral state by callers so
 * the UI never reveals whether a school/resource exists (CP-4).
 */
export async function listSchoolStudents(
  schoolId: string,
): Promise<RosterEntryOut[]> {
  return apiFetch<RosterEntryOut[]>(
    `/school/${encodeURIComponent(schoolId)}/students`,
  );
}

/**
 * GET /school/students/{student_id}/progress — one assigned student's full
 * de-sensitized view (FR-82, CP-3): competency progress + assessment summary
 * codes only, never the raw assessment payload. A 404 (not assigned / no
 * access) is rendered as a neutral not-found state by callers (CP-4).
 */
export async function readStudentProgress(
  studentId: string,
): Promise<StudentProgressOut> {
  return apiFetch<StudentProgressOut>(
    `/school/students/${encodeURIComponent(studentId)}/progress`,
  );
}

/**
 * POST /counseling/sessions — log a counseling session at Tier 1/2/3 (FR-81).
 * The counselor records who they supported and at which tier; the backend
 * stamps `counselor_id` from the authenticated principal.
 */
export async function createCounselingSession(
  payload: CreateSessionRequest,
): Promise<CounselingSessionOut> {
  return apiFetch<CounselingSessionOut>("/counseling/sessions", {
    method: "POST",
    body: payload,
  });
}
