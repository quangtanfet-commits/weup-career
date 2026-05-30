"use client";

import { useTranslations } from "next-intl";

import type {
  CompetencyArea,
  DevPhase,
  ProgressItem,
} from "@/lib/api/endpoints/progress";
import { COMPETENCY_AREAS } from "@/lib/progress/depth";

/**
 * Dev-phase panel (architecture.md §11, FR-23). Shows the learner's current
 * career-development phase per ABCD area. dev_phase is sourced from
 * `GET /me/progress` (each `ProgressItemOut` carries its area's phase — there is
 * no separate GET), so this collapses the progress rows to one phase per area.
 *
 * Read-only in F4: the phase is orthogonal to K-A-R depth (ADR-013). Working
 * users may legitimately hold different phases across areas, so we render one
 * line per area that has data rather than a single global phase.
 */
export function DevPhasePanel({ items }: { items: readonly ProgressItem[] }) {
  const t = useTranslations("progress");
  const areaLabel = useTranslations("progress.area");
  const phaseLabel = useTranslations("progress.devPhase");

  // One phase per area: first row wins (the backend keeps them consistent per area).
  const phaseByArea = new Map<CompetencyArea, DevPhase>();
  for (const item of items) {
    if (!phaseByArea.has(item.area)) {
      phaseByArea.set(item.area, item.dev_phase);
    }
  }

  const rows = COMPETENCY_AREAS.filter((area) => phaseByArea.has(area));

  if (rows.length === 0) {
    return <p className="text-sm text-ink-600">{t("empty")}</p>;
  }

  return (
    <dl className="grid gap-3 sm:grid-cols-3">
      {rows.map((area) => (
        <div
          key={area}
          className="flex flex-col gap-1 rounded-md border bg-white p-4"
        >
          <dt className="text-xs font-medium uppercase tracking-wide text-ink-600">
            {areaLabel(area)}
          </dt>
          <dd className="text-sm font-semibold text-ink-900">
            {phaseLabel(phaseByArea.get(area) as DevPhase)}
          </dd>
        </div>
      ))}
    </dl>
  );
}
