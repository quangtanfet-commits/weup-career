"use client";

import { apiFetch } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

/**
 * Account & data-subject-rights endpoints (architecture.md §11; FR-91, FR-92,
 * Law 91/2025). Every call here is authenticated and SENSITIVE (own profile,
 * password, personal-data export, account deletion), so they run on the
 * **client** with the in-memory bearer token via `apiFetch` — never the
 * server-only `publicFetch`. Colocating them with a `server-only` module would
 * pull `server-only` into the client bundle and break `next build`; this module
 * imports only the client fetch + `import type` shapes (erased at compile time),
 * keeping the server/client boundary intact.
 *
 * Request/response shapes come from the generated OpenAPI schema so the FE↔BE
 * contract is compile-time checked (NFR-20). Note the deliberate asymmetry:
 * the profile is READ at `GET /me/profile` but UPDATED via `PATCH /me`.
 */
export type ProfileOut = components["schemas"]["ProfileOut"];
export type ProfileUpdateRequest = components["schemas"]["ProfileUpdateRequest"];
export type PasswordChangeRequest =
  components["schemas"]["PasswordChangeRequest"];
export type DeletionOut = components["schemas"]["DeletionOut"];
export type DataExport = components["schemas"]["DataExport"];

/** GET /me/profile — the caller's own profile (FR-91 view). */
export async function getProfile(): Promise<ProfileOut> {
  return apiFetch<ProfileOut>("/me/profile");
}

/**
 * PATCH /me — partial update of the editable SAFE profile fields (FR-91). The
 * read is at `/me/profile` but the update target is `/me`; respect the split.
 */
export async function updateProfile(
  payload: ProfileUpdateRequest,
): Promise<ProfileOut> {
  return apiFetch<ProfileOut>("/me", { method: "PATCH", body: payload });
}

/**
 * POST /me/password — change password (FR-91). Requires the current password to
 * authorise; the backend returns 204 No Content on success.
 */
export async function changePassword(
  payload: PasswordChangeRequest,
): Promise<void> {
  await apiFetch<void>("/me/password", { method: "POST", body: payload });
}

/**
 * DELETE /me — soft-delete the caller's account (FR-92, Law 91/2025). The
 * backend acknowledges with a `DeletionOut` stating when the hard purge becomes
 * due, so the UI can show the recovery window explicitly.
 */
export async function deleteAccount(): Promise<DeletionOut> {
  return apiFetch<DeletionOut>("/me", { method: "DELETE" });
}

/** GET /me/export — export all of the caller's personal data (FR-92). */
export async function exportData(): Promise<DataExport> {
  return apiFetch<DataExport>("/me/export");
}

/**
 * GET /me/children/{child_id}/export — guardian-only export of a linked child's
 * data (FR-92). The backend re-checks the guardian link per request (CP-4); the
 * FE gate only hides the surface from non-guardians.
 */
export async function exportChildData(childId: string): Promise<DataExport> {
  return apiFetch<DataExport>(
    `/me/children/${encodeURIComponent(childId)}/export`,
  );
}

/**
 * DELETE /me/children/{child_id} — guardian-only soft-delete of a linked
 * child's account (FR-92). Returns a `DeletionOut` with the recovery window.
 */
export async function deleteChildAccount(
  childId: string,
): Promise<DeletionOut> {
  return apiFetch<DeletionOut>(
    `/me/children/${encodeURIComponent(childId)}`,
    { method: "DELETE" },
  );
}
