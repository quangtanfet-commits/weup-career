"use client";

import { useTranslations } from "next-intl";

import { cn } from "@/lib/utils";
import type {
  Competency,
  Depth,
  ProgressItem,
} from "@/lib/api/endpoints/progress";
import { DEPTHS, groupByArea, isDepthReached } from "@/lib/progress/depth";

/**
 * Competency tree (architecture.md §11, FR-20/21). Renders the fixed 12
 * competencies grouped under the three ABCD areas, each as a collapsible
 * `<details>` exposing its indicators by depth (K→A→R). When a learner's
 * progress is supplied, reached depths are marked (icon + text + colour) so the
 * tree doubles as a progress map.
 *
 * Pure presentation: no control mutates depth here (CP-8 — advancement is a
 * backend write recorded elsewhere). `<details>` keeps it usable without JS.
 */
export function CompetencyTree({
  competencies,
  progress = [],
}: {
  competencies: readonly Competency[];
  progress?: readonly ProgressItem[];
}) {
  const t = useTranslations("progress");
  const area = useTranslations("progress.area");

  if (competencies.length === 0) {
    return <p className="text-sm text-ink-600">{t("empty")}</p>;
  }

  // Map competency_id → achieved depth so indicators can be marked reached.
  const achievedById = new Map<string, Depth | null>(
    progress.map((p) => [p.competency_id, p.depth_achieved]),
  );

  const groups = groupByArea(competencies);

  return (
    <div className="flex flex-col gap-6">
      {groups.map(({ area: areaCode, items }) => (
        <section key={areaCode} className="flex flex-col gap-3">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-ink-600">
            {area(areaCode)}
          </h3>
          <ul className="flex flex-col gap-2">
            {items.map((competency) => (
              <li key={competency.id}>
                <details className="rounded-md border bg-white">
                  <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-ink-900 [&::-webkit-details-marker]:hidden">
                    {competency.name_vi}
                    <span className="ml-2 text-xs font-normal text-ink-600">
                      {competency.code}
                    </span>
                  </summary>
                  <CompetencyIndicators
                    competency={competency}
                    achieved={achievedById.get(competency.id) ?? null}
                  />
                </details>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

function CompetencyIndicators({
  competency,
  achieved,
}: {
  competency: Competency;
  achieved: Depth | null;
}) {
  const t = useTranslations("progress");
  const depthLabel = useTranslations("progress.depth");

  if (competency.indicators.length === 0) {
    return (
      <p className="px-4 pb-3 text-xs text-ink-600">{t("noIndicators")}</p>
    );
  }

  return (
    <div className="border-t px-4 py-3">
      <p className="sr-only">{t("indicatorsLabel")}</p>
      <ul className="flex flex-col gap-2">
        {DEPTHS.flatMap((depth) =>
          competency.indicators
            .filter((indicator) => indicator.depth === depth)
            .map((indicator) => {
              const reached = isDepthReached(depth, achieved);
              return (
                <li
                  key={indicator.id}
                  className="flex items-start gap-2 text-sm"
                >
                  <span
                    aria-hidden="true"
                    className={cn(
                      "mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold",
                      reached
                        ? "bg-success-600 text-white"
                        : "border border-ink-600/30 text-ink-600",
                    )}
                  >
                    {reached ? "✓" : ""}
                  </span>
                  <span className="flex flex-col">
                    <span className="text-[11px] font-medium uppercase text-ink-600">
                      {depthLabel(depth)}
                      <span className="sr-only">
                        {` — ${reached ? t("achievedLabel") : t("notYetLabel")}`}
                      </span>
                    </span>
                    <span className="text-ink-900">
                      {indicator.statement_vi}
                    </span>
                  </span>
                </li>
              );
            }),
        )}
      </ul>
    </div>
  );
}
