"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  createContent,
  getEditorContentItem,
  listEditorContent,
  publishContentVersion,
  type ContentItem,
  type CreateContentRequest,
  type EditorContentFilters,
} from "@/lib/api/endpoints/content-editor";

/**
 * Content-editor data hooks (architecture.md §6.2, group `content`; FR-90).
 * The editor surface is authed (R:content_editor) and sees ALL statuses, so it
 * runs on the client through `apiFetch` (token + status filter) — never the
 * public RSC reads. These are TanStack Query hooks (architecture.md §5.4).
 *
 * Keys are hierarchical: the list key carries the filter so different filters
 * cache separately, and the per-item key lets a published version invalidate
 * just that item plus the list (the FE re-reads the new truth rather than
 * mutating cached rows).
 */
export const contentKeys = {
  list: (filters: EditorContentFilters) =>
    ["editor", "content", "list", filters] as const,
  item: (id: string) => ["editor", "content", "item", id] as const,
};

/** GET /content (editor, with token) — list at any status (FR-90). */
export function useEditorContentList(
  filters: EditorContentFilters = {},
): UseQueryResult<ContentItem[]> {
  return useQuery({
    queryKey: contentKeys.list(filters),
    queryFn: () => listEditorContent(filters),
  });
}

/** GET /content/{id} (editor) — single item at any status for traceability. */
export function useEditorContentItem(
  contentId: string | undefined,
): UseQueryResult<ContentItem> {
  return useQuery({
    queryKey: contentKeys.item(contentId ?? ""),
    queryFn: () => getEditorContentItem(contentId as string),
    enabled: Boolean(contentId),
  });
}

/** POST /content — create a draft; invalidates editor lists so it appears. */
export function useCreateContent(): UseMutationResult<
  ContentItem,
  unknown,
  CreateContentRequest
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateContentRequest) => createContent(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["editor", "content", "list"],
      });
    },
  });
}

/**
 * POST /content/{id}/versions — publish a new version (FR-90). On success both
 * the affected item and the lists are invalidated so the FE re-reads the new
 * published version + archived prior version from the backend.
 */
export function usePublishContentVersion(
  contentId: string,
): UseMutationResult<ContentItem, unknown, void> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => publishContentVersion(contentId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: contentKeys.item(contentId),
      });
      void queryClient.invalidateQueries({
        queryKey: ["editor", "content", "list"],
      });
    },
  });
}
