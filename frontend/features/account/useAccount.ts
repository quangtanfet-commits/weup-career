"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  changePassword,
  deleteAccount,
  deleteChildAccount,
  exportChildData,
  exportData,
  getProfile,
  updateProfile,
  type DataExport,
  type DeletionOut,
  type PasswordChangeRequest,
  type ProfileOut,
  type ProfileUpdateRequest,
} from "@/lib/api/endpoints/account";

/**
 * Account & data-subject-rights hooks (architecture.md §11; FR-91, FR-92). All
 * surfaces are authed + sensitive, so they run on the client through `apiFetch`
 * (the bearer token lives there) — never RSC fetches (architecture.md §5.4).
 * These are TanStack Query hooks (architecture.md §5.4).
 *
 * Profile is a cached query that the update mutation invalidates so the FE
 * re-reads the new truth from the backend. Export/delete are imperative
 * mutations (a one-shot action the user triggers), not cached reads.
 */
export const accountKeys = {
  profile: () => ["account", "profile"] as const,
};

/** GET /me/profile — the caller's own profile (FR-91). */
export function useProfile(): UseQueryResult<ProfileOut> {
  return useQuery({
    queryKey: accountKeys.profile(),
    queryFn: () => getProfile(),
  });
}

/** PATCH /me — update profile; invalidates the cached profile (FR-91). */
export function useUpdateProfile(): UseMutationResult<
  ProfileOut,
  unknown,
  ProfileUpdateRequest
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProfileUpdateRequest) => updateProfile(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: accountKeys.profile() });
    },
  });
}

/** POST /me/password — change password; requires the current password (FR-91). */
export function useChangePassword(): UseMutationResult<
  void,
  unknown,
  PasswordChangeRequest
> {
  return useMutation({
    mutationFn: (payload: PasswordChangeRequest) => changePassword(payload),
  });
}

/** GET /me/export — export the caller's personal data (FR-92). */
export function useExportData(): UseMutationResult<DataExport, unknown, void> {
  return useMutation({
    mutationFn: () => exportData(),
  });
}

/** DELETE /me — soft-delete the caller's account + recovery window (FR-92). */
export function useDeleteAccount(): UseMutationResult<
  DeletionOut,
  unknown,
  void
> {
  return useMutation({
    mutationFn: () => deleteAccount(),
  });
}

/** GET /me/children/{id}/export — guardian-only child data export (FR-92). */
export function useExportChildData(): UseMutationResult<
  DataExport,
  unknown,
  string
> {
  return useMutation({
    mutationFn: (childId: string) => exportChildData(childId),
  });
}

/** DELETE /me/children/{id} — guardian-only child soft-delete (FR-92). */
export function useDeleteChildAccount(): UseMutationResult<
  DeletionOut,
  unknown,
  string
> {
  return useMutation({
    mutationFn: (childId: string) => deleteChildAccount(childId),
  });
}
