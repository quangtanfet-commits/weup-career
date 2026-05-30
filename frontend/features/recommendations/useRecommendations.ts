"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  confirmRecommendation,
  generateRecommendation,
  getRecommendation,
  type ConfirmRequest,
  type RecommendationOut,
} from "@/lib/api/endpoints/recommendations";

/**
 * F5 data hooks (architecture.md §11, FR-60..63, CP-5/CP-6). Personal/authed
 * reads-and-writes run on the client through `apiFetch` (token + consent gate
 * live there), so these are TanStack Query hooks — never RSC fetches
 * (architecture.md §5.4).
 *
 * Query keys are stable, hierarchical arrays so a successful confirm can
 * invalidate exactly the affected recommendation read (CP-5: the backend
 * records the human decision, the FE just re-reads the new truth rather than
 * optimistically mutating cached state).
 */
export const recommendationKeys = {
  all: ["recommendations"] as const,
  detail: (recoId: string) => ["recommendations", recoId] as const,
};

/**
 * GET /recommendations/{reco_id} — read a single recommendation (FR-61). 404
 * (no access / not found) surfaces as a query error so the page can render a
 * neutral not-found state (CP-4 existence-hiding).
 */
export function useRecommendation(
  recoId: string,
): UseQueryResult<RecommendationOut> {
  return useQuery({
    queryKey: recommendationKeys.detail(recoId),
    queryFn: () => getRecommendation(recoId),
    // A read failure (404) must not be hammered; surface it immediately.
    retry: false,
  });
}

/**
 * POST /recommendations — generate a new recommendation (FR-60, CP-6). On
 * success we seed the detail query cache with the returned recommendation so
 * the detail page can render it without an extra round-trip.
 */
export function useGenerateRecommendation(): UseMutationResult<
  RecommendationOut,
  unknown,
  void
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => generateRecommendation(),
    onSuccess: (reco) => {
      queryClient.setQueryData(recommendationKeys.detail(reco.id), reco);
    },
  });
}

/**
 * POST /recommendations/{reco_id}/confirm — record the explicit human decision
 * (CP-5). There is intentionally NO optimistic update: on success we invalidate
 * the recommendation read so the UI re-reads the confirmed truth from the
 * backend (architecture.md §5.5). The decision only ever fires from an explicit
 * user click in `HumanConfirmAction`, never automatically.
 */
export function useConfirmRecommendation(
  recoId: string,
): UseMutationResult<RecommendationOut, unknown, ConfirmRequest> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ConfirmRequest) => confirmRecommendation(recoId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: recommendationKeys.detail(recoId),
      });
    },
  });
}
