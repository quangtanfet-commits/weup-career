import type { components, operations } from "@/lib/api/schema";
import { publicFetch } from "@/lib/api/server";

/**
 * Public content endpoints (architecture.md §6.2, group `content`, rows marked
 * **P** = anonymous-readable). These back the public Điều 5(a)/(c)/(d) content
 * pages and are fetched server-side with no token (BE-1).
 *
 * Important boundary (§6.2): only `GET /content` (the list) is public and
 * **published-only** — anonymous callers cannot pass `?status=` to see drafts.
 * `GET /content/{id}` is editor-only (Bearer, R:editor) and is therefore NOT
 * used here. The public content-detail page resolves an item from the published
 * list instead, which keeps the anonymous-readable invariant intact.
 */
export type ContentItem = components["schemas"]["ContentItemOut"];

type ContentQuery = NonNullable<
  operations["list_content"]["parameters"]["query"]
>;

export interface ContentFilters {
  readonly dieu5_code?: ContentQuery["dieu5_code"];
  readonly competency_code?: ContentQuery["competency_code"];
  readonly dev_phase?: ContentQuery["dev_phase"];
  readonly school_level?: ContentQuery["school_level"];
}

function toQuery(filters: ContentFilters): Record<string, string | undefined> {
  // `status` is intentionally omitted: the anonymous list is published-only and
  // forwarding a status filter would attempt to read non-published rows.
  return {
    dieu5_code: filters.dieu5_code ?? undefined,
    competency_code: filters.competency_code ?? undefined,
    dev_phase: filters.dev_phase ?? undefined,
    school_level: filters.school_level ?? undefined,
  };
}

/** GET /content — public, published-only content list. */
export async function listContent(
  filters: ContentFilters = {},
): Promise<ContentItem[]> {
  return publicFetch<ContentItem[]>("/content", { query: toQuery(filters) });
}

/**
 * Resolve a single published content item by id from the public list.
 *
 * There is no anonymous `GET /content/{id}` (that route is editor-only), so the
 * public detail page reads the published list and selects by id. Returns `null`
 * when no published item matches, letting the page render `notFound()`.
 */
export async function getPublicContentItem(
  contentId: string,
): Promise<ContentItem | null> {
  const items = await listContent();
  return items.find((item) => item.id === contentId) ?? null;
}
