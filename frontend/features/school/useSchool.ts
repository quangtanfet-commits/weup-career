"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  assignMember,
  createClass,
  listClasses,
  type AssignMemberRequest,
  type CreateClassRequest,
  type MembershipOut,
  type SchoolClassOut,
} from "@/lib/api/endpoints/school";

/**
 * School-admin data hooks (architecture.md §6.2, group `school`; FR-80, CP-4).
 * Authed reads/writes run on the client through `apiFetch` (token lives there),
 * so these are TanStack Query hooks — never RSC fetches (architecture.md §5.4).
 *
 * Query keys are hierarchical and scoped by `schoolId` so a class created in one
 * school invalidates only that school's class list (the FE re-reads the new
 * truth from the backend rather than mutating the cache locally).
 */
export const schoolKeys = {
  classes: (schoolId: string) => ["school", schoolId, "classes"] as const,
};

/** GET /school/{id}/classes — classes in the admin's school. Disabled until a school id is known. */
export function useClasses(
  schoolId: string | undefined,
): UseQueryResult<SchoolClassOut[]> {
  return useQuery({
    queryKey: schoolKeys.classes(schoolId ?? ""),
    queryFn: () => listClasses(schoolId as string),
    enabled: Boolean(schoolId),
  });
}

/** POST /school/{id}/classes — create a class; invalidates that school's class list. */
export function useCreateClass(
  schoolId: string,
): UseMutationResult<SchoolClassOut, unknown, CreateClassRequest> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateClassRequest) => createClass(schoolId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: schoolKeys.classes(schoolId),
      });
    },
  });
}

/**
 * POST /school/{id}/members — assign a student/counselor. A new class-scoped
 * membership can affect roster views, so the school's class list is invalidated
 * to keep dependent reads fresh.
 */
export function useAssignMember(
  schoolId: string,
): UseMutationResult<MembershipOut, unknown, AssignMemberRequest> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: AssignMemberRequest) =>
      assignMember(schoolId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: schoolKeys.classes(schoolId),
      });
    },
  });
}
