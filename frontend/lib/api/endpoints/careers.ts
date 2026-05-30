import type { components, operations } from "@/lib/api/schema";
import { publicFetch } from "@/lib/api/server";

/**
 * Public career-library endpoints (architecture.md §6.2, group `careers`).
 * These are **anonymous-readable** (BE-1), so they are fetched server-side with
 * no token for SEO/ISR. The response types come straight from the generated
 * OpenAPI schema, keeping the FE↔BE contract compile-time checked (NFR-20).
 */
export type CareerSummary = components["schemas"]["CareerSummaryOut"];
export type CareerDetail = components["schemas"]["CareerDetailOut"];

export type RiasecCode = components["schemas"]["RiasecCode"];
export type TrainingLevel = components["schemas"]["TrainingLevel"];
export type PathwayType = components["schemas"]["PathwayType"];

type CareerQuery = NonNullable<
  operations["list_careers"]["parameters"]["query"]
>;

export interface CareerFilters {
  readonly riasec?: CareerQuery["riasec"];
  readonly field?: CareerQuery["field"];
  readonly training_level?: CareerQuery["training_level"];
  readonly pathway_type?: CareerQuery["pathway_type"];
}

function toQuery(filters: CareerFilters): Record<string, string | undefined> {
  return {
    riasec: filters.riasec ?? undefined,
    field: filters.field ?? undefined,
    training_level: filters.training_level ?? undefined,
    pathway_type: filters.pathway_type ?? undefined,
  };
}

/** GET /careers — public library list (published-only, enforced server-side). */
export async function listCareers(
  filters: CareerFilters = {},
): Promise<CareerSummary[]> {
  return publicFetch<CareerSummary[]>("/careers", { query: toQuery(filters) });
}

/** GET /careers/{careerId} — public career detail; throws ApiError 404 if unknown. */
export async function getCareer(careerId: string): Promise<CareerDetail> {
  return publicFetch<CareerDetail>(`/careers/${encodeURIComponent(careerId)}`);
}
