"use client";

import {
  useMutation,
  useQuery,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  listSchoolStudents,
  readStudentProgress,
  createCounselingSession,
  type RosterEntryOut,
  type StudentProgressOut,
  type CounselingSessionOut,
  type CreateSessionRequest,
} from "@/lib/api/endpoints/counseling";

/**
 * F7 counselor data hooks (architecture.md §6.2, §10; FR-80..83, CP-3/CP-4).
 * All reads are personal/authed and run on the client through `apiFetch` (token
 * lives there), so these are TanStack Query hooks — never RSC fetches
 * (architecture.md §5.4). The counselor only ever reads de-sensitized shapes
 * (CP-3); there is no cached raw assessment payload.
 *
 * Query keys are stable, hierarchical arrays scoped by school/student id.
 * `retry: false` keeps a 403/404 (not authorised / [CRED_3D71D2A2]) from being retried —
 * callers map it to a neutral not-found state without leaking existence (CP-4).
 */
export const counselingKeys = {
  roster: (schoolId: string) => ["school", schoolId, "students"] as const,
  student: (studentId: string) =>
    ["school", "students", studentId, "progress"] as const,
};

/** GET /school/{school_id}/students — de-sensitized roster (FR-82, CP-3). */
export function useSchoolStudents(
  schoolId: string | null,
): UseQueryResult<RosterEntryOut[]> {
  return useQuery({
    queryKey: counselingKeys.roster(schoolId ?? ""),
    queryFn: () => listSchoolStudents(schoolId as string),
    enabled: schoolId !== null && schoolId !== "",
    retry: false,
  });
}

/** GET /school/students/{student_id}/progress — one student's de-sensitized view (FR-82, CP-3). */
export function useStudentProgress(
  studentId: string,
): UseQueryResult<StudentProgressOut> {
  return useQuery({
    queryKey: counselingKeys.student(studentId),
    queryFn: () => readStudentProgress(studentId),
    enabled: studentId !== "",
    retry: false,
  });
}

/**
 * POST /counseling/sessions — log a Tier 1/2/3 counseling session (FR-81). No
 * read query is invalidated: sessions are append-only records and no list view
 * of them is part of this slice.
 */
export function useCreateCounselingSession(): UseMutationResult<
  CounselingSessionOut,
  unknown,
  CreateSessionRequest
> {
  return useMutation({
    mutationFn: (payload: CreateSessionRequest) =>
      createCounselingSession(payload),
  });
}
