import Link from "next/link";
import { getTranslations } from "next-intl/server";

import type {
  CareerFilters as CareerFilterValues,
  PathwayType,
  RiasecCode,
  TrainingLevel,
} from "@/lib/api/endpoints/careers";

/**
 * RSC-friendly career filters (architecture.md §4.4 — `CareerFilters`).
 *
 * Public pages are anonymous Server Components, so this is a plain GET `<form>`:
 * submitting navigates to `/careers?riasec=…&training_level=…` and the page
 * re-renders server-side with the new query. No client JS, no token — it works
 * with JavaScript disabled, matching the public/SEO contract (§3, §5.4).
 */
const RIASEC_CODES: readonly RiasecCode[] = ["R", "I", "A", "S", "E", "C"];
const TRAINING_LEVELS: readonly TrainingLevel[] = [
  "secondary",
  "vocational",
  "college",
  "university",
  "postgraduate",
];
const PATHWAY_TYPES: readonly PathwayType[] = [
  "academic",
  "vocational_secondary",
  "gdnn",
  "labor",
];

export async function CareerFilters({
  selected,
}: {
  selected: CareerFilterValues;
}) {
  const t = await getTranslations("careers");
  const common = await getTranslations("common");
  const trainingLevel = await getTranslations("trainingLevel");
  const pathwayType = await getTranslations("pathwayType");

  return (
    <form
      method="get"
      action="/careers"
      aria-label={t("filtersHeading")}
      className="mt-8 grid gap-4 rounded-md border bg-white p-4 sm:grid-cols-3"
    >
      <h2 className="sr-only">{t("filtersHeading")}</h2>

      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-ink-900">{t("riasecLabel")}</span>
        <select
          name="riasec"
          defaultValue={selected.riasec ?? ""}
          className="rounded-sm border px-2 py-1.5 text-ink-900"
        >
          <option value="">{common("all")}</option>
          {RIASEC_CODES.map((code) => (
            <option key={code} value={code}>
              {code}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-ink-900">
          {t("trainingLevelLabel")}
        </span>
        <select
          name="training_level"
          defaultValue={selected.training_level ?? ""}
          className="rounded-sm border px-2 py-1.5 text-ink-900"
        >
          <option value="">{common("all")}</option>
          {TRAINING_LEVELS.map((level) => (
            <option key={level} value={level}>
              {trainingLevel(level)}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-ink-900">{t("pathwayLabel")}</span>
        <select
          name="pathway_type"
          defaultValue={selected.pathway_type ?? ""}
          className="rounded-sm border px-2 py-1.5 text-ink-900"
        >
          <option value="">{common("all")}</option>
          {PATHWAY_TYPES.map((type) => (
            <option key={type} value={type}>
              {pathwayType(type)}
            </option>
          ))}
        </select>
      </label>

      <div className="flex items-end gap-3 sm:col-span-3">
        <button
          type="submit"
          className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground hover:bg-primary-700"
        >
          {t("applyFilters")}
        </button>
        <Link
          href="/careers"
          className="text-sm font-medium text-primary-700 hover:underline"
        >
          {t("clearFilters")}
        </Link>
      </div>
    </form>
  );
}
