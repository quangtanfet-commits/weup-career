"use client";

import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

/**
 * School-admin endpoints (architecture.md §6.2, group `school`; FR-80). A
 * `school_admin` manages classes and assigns members (students / counselors)
 * **within their own `school_id`** — every call is scoped by the `school_id`
 * path segment and the backend re-checks membership per request (CP-4), so the
 * FE never relies on the path alone for authority.
 *
 * Request/response shapes come from the generated OpenAPI schema so the FE↔BE
 * contract is compile-time checked (NFR-20). All calls run on the client with
 * the in-memory bearer token (Bearer, R:school_admin).
 */
export type SchoolClassOut = components["schemas"]["SchoolClassOut"];
export type CreateClassRequest = components["schemas"]["CreateClassRequest"];
export type AssignMemberRequest = components["schemas"]["AssignMemberRequest"];
export type MembershipOut = components["schemas"]["MembershipOut"];
export type SchoolRole = components["schemas"]["SchoolRole"];

/** GET /school/{school_id}/classes — list classes in the admin's school. */
export async function listClasses(schoolId: string): Promise<SchoolClassOut[]> {
  return apiFetch<SchoolClassOut[]>(
    `/school/${encodeURIComponent(schoolId)}/classes`,
  );
}

/** POST /school/{school_id}/classes — create a class (FR-80). */
export async function createClass(
  schoolId: string,
  payload: CreateClassRequest,
): Promise<SchoolClassOut> {
  return apiFetch<SchoolClassOut>(
    `/school/${encodeURIComponent(schoolId)}/classes`,
    { method: "POST", body: payload },
  );
}

/**
 * POST /school/{school_id}/members — assign a user as student or counselor in
 * the school, optionally scoped to a class (FR-80). The backend constrains the
 * `role` to the assignable school roles and rejects anything else.
 */
export async function assignMember(
  schoolId: string,
  payload: AssignMemberRequest,
): Promise<MembershipOut> {
  return apiFetch<MembershipOut>(
    `/school/${encodeURIComponent(schoolId)}/members`,
    { method: "POST", body: payload },
  );
}
