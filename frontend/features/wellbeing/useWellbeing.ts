"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  createSupportRequest,
  listSupportRequests,
  type SupportRequestCreate,
  type SupportRequestOut,
} from "@/lib/api/endpoints/wellbeing";

/**
 * Wellbeing data hooks (architecture.md §6.2, group `wellbeing`; FR-70/FR-71,
 * NL4). Support requests are authed + personal, so they run on the client
 * through `apiFetch` (the bearer token lives there) — never RSC fetches
 * (architecture.md §5.4). These are TanStack Query hooks (ADR-004).
 *
 * The list is a cached query; the create mutation invalidates it so the learner
 * sees their new request appear without the parent coordinating a refresh. The
 * records are routing-only (NG-03), so the default cache policy is fine — no
 * sensitive per-query opt-out is needed.
 */
export const wellbeingKeys = {
  supportRequests: () => ["wellbeing", "support-requests"] as const,
};

/** GET /wellbeing/support-requests — the signed-in learner's own requests. */
export function useSupportRequests(): UseQueryResult<SupportRequestOut[]> {
  return useQuery({
    queryKey: wellbeingKeys.supportRequests(),
    queryFn: () => listSupportRequests(),
  });
}

/**
 * POST /wellbeing/support-request — create a request; invalidates the list so
 * the new request appears (FR-71).
 */
export function useCreateSupportRequest(): UseMutationResult<
  SupportRequestOut,
  unknown,
  SupportRequestCreate
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SupportRequestCreate) =>
      createSupportRequest(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: wellbeingKeys.supportRequests(),
      });
    },
  });
}
