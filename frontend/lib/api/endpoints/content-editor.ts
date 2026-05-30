"use client";

import { apiFetch } from "@/lib/api/client";
import type { components, operations } from "@/lib/api/schema";

/**
 * Editor (authenticated, R:content_editor) content endpoints — FR-90.
 *
 * These run on the **client** with the in-memory bearer token (`apiFetch`) and
 * are deliberately kept in a separate module from the public, server-side reads
 * in `./content`. That module imports `server-only` (`publicFetch`); colocating
 * the client editor calls there would pull `server-only` into the client bundle
 * and break `next build`. The split keeps the server/client boundary clean.
 *
 * The editor sees content across ALL statuses for traceability, so it uses
 * `GET /content/{id}` (Bearer, R:editor) — NOT the published-only public list.
 */
export type { ContentItem } from "./content";

export type CreateContentRequest =
  components["schemas"]["CreateContentRequest"];

export type ContentStatus = components["schemas"]["ContentStatus"];

type EditorContentQuery = NonNullable<
  operations["list_content"]["parameters"]["query"]
>;

export interface EditorContentFilters {
  readonly dieu5_code?: EditorContentQuery["dieu5_code"];
  readonly competency_code?: EditorContentQuery["competency_code"];
  readonly dev_phase?: EditorContentQuery["dev_phase"];
  readonly school_level?: EditorContentQuery["school_level"];
  readonly status?: EditorContentQuery["status"];
}

type ContentItemOut = components["schemas"]["ContentItemOut"];

/**
 * GET /content — editor list. The same route is public/published-only when
 * called anonymously, but the editor calls it WITH a bearer token and MAY pass
 * `?status=` to review drafts/archived rows (the backend authorises that filter
 * only for an editor). Fetched client-side so the token is attached.
 */
export async function listEditorContent(
  filters: EditorContentFilters = {},
): Promise<ContentItemOut[]> {
  return apiFetch<ContentItemOut[]>("/content", {
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
): Promise<ContentItemOut> {
  return apiFetch<ContentItemOut>(`/content/${encodeURIComponent(contentId)}`);
}

/** POST /content — create a new draft with the five mandatory tags (FR-90). */
export async function createContent(
  payload: CreateContentRequest,
): Promise<ContentItemOut> {
  return apiFetch<ContentItemOut>("/content", {
    method: "POST",
    body: payload,
  });
}

/**
 * POST /content/{id}/versions — publish a new version; the backend archives the
 * prior published version (FR-90). The route takes no request body — publishing
 * promotes the item's current draft state to the next published version.
 */
export async function publishContentVersion(
  contentId: string,
): Promise<ContentItemOut> {
  return apiFetch<ContentItemOut>(
    `/content/${encodeURIComponent(contentId)}/versions`,
    { method: "POST" },
  );
}
