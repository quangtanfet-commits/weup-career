import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { CareerCard } from "@/features/careers/CareerCard";
import { CareerFilters } from "@/features/careers/CareerFilters";
import {
  listCareers,
  type CareerFilters as CareerFilterValues,
  type CareerSummary,
  type PathwayType,
  type RiasecCode,
  type TrainingLevel,
} from "@/lib/api/endpoints/careers";

/**
 * Public career library (Luồng 3, Điều 5(a)) — architecture.md §3 `(public)/careers`.
 *
 * A **React Server Component**: it reads the filter query string, fetches
 * `GET /api/v1/careers` **anonymously** server-side (no Authorization header,
 * BE-1; published-only enforced by the backend) and renders the results with an
 * RSC GET-form filter. No token ever reaches this path (§5.4).
 */
export const metadata: Metadata = {
  title: "Thư viện nghề nghiệp",
  description:
    "Khám phá nghề nghiệp theo Điều 5(a) — thông tin công khai, không cần đăng nhập.",
};

// Cap the rendered list so an empty or very large dataset both render cleanly.
const MAX_VISIBLE = 120;

const RIASEC_CODES = new Set<RiasecCode>(["R", "I", "A", "S", "E", "C"]);
const TRAINING_LEVELS = new Set<TrainingLevel>([
  "secondary",
  "vocational",
  "college",
  "university",
  "postgraduate",
]);
const PATHWAY_TYPES = new Set<PathwayType>([
  "academic",
  "vocational_secondary",
  "gdnn",
  "labor",
]);

/** Read a single value out of a Next.js searchParams entry (string | string[]). */
function first(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

/**
 * Parse raw query strings into typed filters, dropping anything that is not a
 * valid enum member so a hand-edited URL can never produce a 422 from the API.
 */
function parseFilters(
  params: Record<string, string | string[] | undefined>,
): CareerFilterValues {
  const riasec = first(params.riasec);
  const trainingLevel = first(params.training_level);
  const pathwayType = first(params.pathway_type);
  const field = first(params.field);

  return {
    riasec:
      riasec && RIASEC_CODES.has(riasec as RiasecCode)
        ? (riasec as RiasecCode)
        : undefined,
    training_level:
      trainingLevel && TRAINING_LEVELS.has(trainingLevel as TrainingLevel)
        ? (trainingLevel as TrainingLevel)
        : undefined,
    pathway_type:
      pathwayType && PATHWAY_TYPES.has(pathwayType as PathwayType)
        ? (pathwayType as PathwayType)
        : undefined,
    field: field && field.trim() !== "" ? field : undefined,
  };
}

export default async function CareerLibraryPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const t = await getTranslations("careers");
  const filters = parseFilters(await searchParams);

  let careers: CareerSummary[] = [];
  let failed = false;
  try {
    careers = await listCareers(filters);
  } catch {
    failed = true;
  }

  // Await the async child Server Component so the whole tree resolves in one
  // pass (Next.js composes this the same way; it also keeps the page testable
  // without a streaming RSC renderer).
  const filtersNode = await CareerFilters({ selected: filters });

  return (
    <main className="mx-auto max-w-5xl px-4 py-12">
      <h1 className="text-3xl font-bold text-ink-900">{t("title")}</h1>
      <p className="mt-2 max-w-2xl text-ink-600">{t("subtitle")}</p>

      {filtersNode}

      {failed ? (
        <p role="alert" className="mt-8 text-danger-600">
          {t("loadError")}
        </p>
      ) : careers.length === 0 ? (
        <p className="mt-8 text-ink-600">{t("empty")}</p>
      ) : (
        <ul className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {careers.slice(0, MAX_VISIBLE).map((career) => (
            <li key={career.id}>
              <CareerCard career={career} />
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
