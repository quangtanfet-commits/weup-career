import { QueryClient } from "@tanstack/react-query";

/**
 * Default QueryClient (ADR-004 / architecture.md §5.5). Personal REST data is
 * cached normally; sensitive queries opt out per-query with
 * `staleTime: 0, gcTime: 0` (helpers added in later slices), never globally.
 */
export function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60_000,
        retry: 1,
        refetchOnWindowFocus: false,
      },
    },
  });
}
