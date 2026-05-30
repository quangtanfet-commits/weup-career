import type { components } from "@/lib/api/schema";
import { publicFetch } from "@/lib/api/server";

/**
 * Public career-library endpoints (architecture.md §6.2, group `careers`).
 * These are **anonymous-readable** (BE-1), so they are fetched server-side with
 * no token for SEO/ISR. The response types come straight from the generated
 * OpenAPI schema, keeping the FE↔BE contract compile-time checked (NFR-20).
 */
export type CareerSummary = components["schemas"]["CareerSummaryOut"];
export type CareerDetail = components["schemas"]["CareerDetailOut"];

export interface CareerFilters {
  readonly riasec?: string;
  readonly field?: string;
  readonly training_level?: string;
  readonly pathway_type?: string;
}

/** GET /careers — public library list (published-only, enforced server-side). */
export async function listCareers(
  filters: CareerFilters = {},
): Promise<CareerSummary[]> {
  return publicFetch<CareerSummary[]>("/careers", { query: { ...filters } });
}

/** GET /careers/{careerId} — public career detail; throws ApiError 404 if unknown. */
export async function getCareer(careerId: string): Promise<CareerDetail> {
  return publicFetch<CareerDetail>(
    `/careers/${encodeURIComponent(careerId)}`,
  );
}
