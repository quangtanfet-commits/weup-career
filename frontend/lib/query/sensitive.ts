"use client";

import {
  useQuery,
  type QueryKey,
  type UseQueryOptions,
  type UseQueryResult,
} from "@tanstack/react-query";

/**
 * No-cache query helper for **sensitive** data (architecture.md §5.5, CP-3).
 *
 * Assessment results (`is_sensitive=true`) must not be cached on the client:
 * each view is one audited backend read, so reading "again" must hit the API
 * again rather than replay a cached value. This forces:
 *  - `staleTime: 0` + `gcTime: 0` — never considered fresh, dropped on unmount;
 *  - `retry: false` — a 401/403 must surface immediately, not be hammered;
 *  - `refetchOnWindowFocus: false` — no implicit extra audited reads on focus.
 *
 * These options are fixed here and cannot be overridden by callers, so a feature
 * can never accidentally re-enable caching for a sensitive query.
 */
export function useSensitiveQuery<TData>(
  key: QueryKey,
  queryFn: () => Promise<TData>,
  options?: Pick<UseQueryOptions<TData, Error, TData, QueryKey>, "enabled">,
): UseQueryResult<TData, Error> {
  return useQuery<TData, Error, TData, QueryKey>({
    queryKey: key,
    queryFn,
    enabled: options?.enabled,
    staleTime: 0,
    gcTime: 0,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnMount: "always",
  });
}
