import { getTranslations } from "next-intl/server";

import type { CareerDetail as CareerDetailData } from "@/lib/api/endpoints/careers";

/**
 * Public career-detail view (architecture.md §4.4 — `CareerDetail`, RSC-friendly).
 * Renders the published `CareerDetailOut` returned by `GET /careers/{id}`. All
 * prose comes from the backend (versioned by school_level); this only lays it
 * out (§9 — FE does not translate versioned content).
 */
export async function CareerDetail({ career }: { career: CareerDetailData }) {
  const t = await getTranslations("careerDetail");
  const trainingLevel = await getTranslations("trainingLevel");
  const pathwayType = await getTranslations("pathwayType");

  return (
    <article className="mt-6 flex flex-col gap-8">
      <header className="flex flex-col gap-3">
        <h1 className="text-3xl font-bold text-ink-900">{career.name}</h1>
        <dl className="flex flex-wrap gap-x-8 gap-y-2 text-sm">
          <div className="flex gap-2">
            <dt className="font-medium text-ink-600">{t("fieldLabel")}:</dt>
            <dd className="text-ink-900">{career.field}</dd>
          </div>
          <div className="flex gap-2">
            <dt className="font-medium text-ink-600">
              {t("trainingLevelLabel")}:
            </dt>
            <dd className="text-ink-900">
              {trainingLevel(career.training_level)}
            </dd>
          </div>
        </dl>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-ink-600">
            {t("riasecLabel")}:
          </span>
          {career.riasec_codes.map((code) => (
            <span
              key={code}
              className="rounded-full bg-primary-50 px-2.5 py-0.5 text-xs font-medium text-primary-700"
            >
              {code}
            </span>
          ))}
        </div>
      </header>

      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold text-ink-900">
          {t("laborMarketLabel")}
        </h2>
        <p className="leading-relaxed text-ink-900">
          {career.labor_market_outlook}
        </p>
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold text-ink-900">
          {t("trainingPathsLabel")}
        </h2>
        <p className="leading-relaxed text-ink-900">{career.training_paths}</p>
      </section>

      {career.required_competencies.length > 0 ? (
        <section className="flex flex-col gap-2">
          <h2 className="text-lg font-semibold text-ink-900">
            {t("requiredCompetenciesLabel")}
          </h2>
          <ul className="flex flex-wrap gap-2">
            {career.required_competencies.map((code) => (
              <li
                key={code}
                className="rounded-full border px-2.5 py-0.5 text-xs font-medium text-secondary-700"
              >
                {code}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {career.pathways.length > 0 ? (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-semibold text-ink-900">
            {t("pathwaysLabel")}
          </h2>
          <ul className="flex flex-col gap-3">
            {career.pathways.map((pathway) => (
              <li
                key={pathway.id}
                className="rounded-md border bg-white p-4 shadow-sm"
              >
                <p className="font-medium text-ink-900">
                  {pathway.name}{" "}
                  <span className="ml-1 rounded-full bg-primary-50 px-2 py-0.5 text-xs font-medium text-primary-700">
                    {pathwayType(pathway.type)}
                  </span>
                </p>
                <p className="mt-1 text-sm text-ink-600">
                  {pathway.description}
                </p>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <p className="text-xs text-ink-600">
        {t("sourceLabel")}: {career.source_ref}
      </p>
    </article>
  );
}
