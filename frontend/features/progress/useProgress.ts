"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  listCompetencies,
  getMyProgress,
  recordIndicator,
  setDevPhase,
  type Competency,
  type ProgressItem,
  type RecordIndicatorOut,
  type RecordIndicatorRequest,
  type DevPhaseOut,
  type SetDevPhaseRequest,
} from "@/lib/api/endpoints/progress";

/**
 * F4 data hooks (architecture.md §11, FR-20..24, CP-8). Personal/authed reads
 * run on the client through `apiFetch` (token + consent gate live there), so
 * these are TanStack Query hooks — never RSC fetches (architecture.md §5.4).
 *
 * Query keys are stable, hierarchical arrays so a successful write can
 * invalidate the affected read precisely (CP-8: the backend advances depth, the
 * FE just re-reads the new truth rather than mutating cached progress locally).
 */
export const progressKeys = {
  competencies: ["competencies"] as const,
  myProgress: ["me", "progress"] as const,
};

/** GET /competencies — the fixed 12-competency tree (FR-20/21). Static, so cached long. */
export function useCompetencies(): UseQueryResult<Competency[]> {
  return useQuery({
    queryKey: progressKeys.competencies,
    queryFn: () => listCompetencies(),
    // The competency tree is fixed reference data; it does not change per session.
    staleTime: Infinity,
  });
}

/** GET /me/progress — the learner's (competency, depth) coordinates + dev_phase (FR-22/23). */
export function useMyProgress(): UseQueryResult<ProgressItem[]> {
  return useQuery({
    queryKey: progressKeys.myProgress,
    queryFn: () => getMyProgress(),
  });
}

/**
 * POST /me/progress/indicators — record an achieved indicator (FR-24, CP-8). On
 * success we invalidate `me/progress` so the viz re-reads the (possibly
 * advanced) depth from the backend, never advancing it client-side.
 */
export function useRecordIndicator(): UseMutationResult<
  RecordIndicatorOut,
  unknown,
  RecordIndicatorRequest
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RecordIndicatorRequest) => recordIndicator(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: progressKeys.myProgress });
    },
  });
}

/**
 * POST /me/progress/dev-phase — record a (possibly deviating) dev_phase for one
 * area (FR-23). Invalidates `me/progress` since the dev_phase is surfaced there.
 */
export function useSetDevPhase(): UseMutationResult<
  DevPhaseOut,
  unknown,
  SetDevPhaseRequest
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SetDevPhaseRequest) => setDevPhase(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: progressKeys.myProgress });
    },
  });
}
