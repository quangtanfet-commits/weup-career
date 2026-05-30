"use client";

import { useTranslations } from "next-intl";

/**
 * RationalePanel (architecture.md §4.4, §7 CP-6; FR-61). The explanation is a
 * **mandatory** part of every recommendation: a recommendation may never be
 * shown without its reason. This panel renders the backend `rationale` text
 * with a clear heading so the learner always sees *why* a suggestion was made.
 *
 * CP-6 enforcement lives in the parent `RecommendationCard`: if `rationale` is
 * missing/empty the card renders an error state instead of this panel, so this
 * component is only ever given a non-empty rationale to display.
 */
export function RationalePanel({ rationale }: { rationale: string }) {
  const t = useTranslations("recommendations");

  return (
    <section
      aria-label={t("rationaleTitle")}
      className="flex flex-col gap-2 rounded-md border border-primary-600/20 bg-primary-50 p-4"
    >
      <h4 className="text-sm font-semibold text-primary-700">
        {t("rationaleTitle")}
      </h4>
      <p className="whitespace-pre-wrap text-sm text-ink-900">{rationale}</p>
    </section>
  );
}
