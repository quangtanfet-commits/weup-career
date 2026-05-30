import { apiFetch } from "@/lib/api/client";
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

/* ----------------------------------------------------------------------------
 * Editor (authenticated, R:content_editor) endpoints — FR-90.
 *
 * Unlike the public reads above (server-side, no token), the editor surface
 * runs on the **client** with the in-memory bearer token (`apiFetch`). The
 * editor sees content across ALL statuses for traceability, so it uses
 * `GET /content/{id}` (Bearer, R:editor) — NOT the published-only public list.
 * ------------------------------------------------------------------------- */
export type CreateContentRequest =
  components["schemas"]["CreateContentRequest"];

type EditorContentQuery = NonNullable<
  operations["list_content"]["parameters"]["query"]
>;
export type ContentStatus = components["schemas"]["ContentStatus"];

export interface EditorContentFilters {
  readonly dieu5_code?: EditorContentQuery["dieu5_code"];
  readonly competency_code?: EditorContentQuery["competency_code"];
  readonly dev_phase?: EditorContentQuery["dev_phase"];
  readonly school_level?: EditorContentQuery["school_level"];
  readonly status?: EditorContentQuery["status"];
}

/**
 * GET /content — editor list. The same route is public/published-only when
 * called anonymously, but the editor calls it WITH a bearer token and MAY pass
 * `?status=` to review drafts/archived rows (the backend authorises that filter
 * only for an editor). Fetched client-side so the token is attached.
 */
export async function listEditorContent(
  filters: EditorContentFilters = {},
): Promise<ContentItem[]> {
  return apiFetch<ContentItem[]>("/content", {
    query: {
      dieu5_code: filters.dieu5_code ?? undefined,
      competency_code: filters.competency_code ?? undefined,
      dev_phase: filters.dev_phase ?? undefined,
      school_level: filters.school_level ?? undefined,
      status: filters.status ?? undefined,
    },
  });
}

/**
 * GET /content/{id} — fetch a single content row at ANY status (editor
 * traceability). This route is Bearer, R:editor (not anonymous-readable), so it
 * is the editor's way to inspect a draft/archived item the public list hides.
 */
export async function getEditorContentItem(
  contentId: string,
): Promise<ContentItem> {
  return apiFetch<ContentItem>(`/content/${encodeURIComponent(contentId)}`);
}

/** POST /content — create a new draft with the five mandatory tags (FR-90). */
export async function createContent(
  payload: CreateContentRequest,
): Promise<ContentItem> {
  return apiFetch<ContentItem>("/content", { method: "POST", body: payload });
}

/**
 * POST /content/{id}/versions — publish a new version; the backend archives the
 * prior published version (FR-90). The route takes no request body — publishing
 * promotes the item's current draft state to the next published version.
 */
export async function publishContentVersion(
  contentId: string,
): Promise<ContentItem> {
  return apiFetch<ContentItem>(
    `/content/${encodeURIComponent(contentId)}/versions`,
    { method: "POST" },
  );
}
