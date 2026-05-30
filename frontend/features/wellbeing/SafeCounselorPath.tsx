"use client";

import { useTranslations } from "next-intl";

/**
 * Safe counselor path (architecture.md §4, FR-71; NL4, Tier 3).
 *
 * An always-visible, non-clinical panel that tells the learner support from a
 * real person (a school counselor — Tier 3) is available and how reaching out
 * works. It deliberately makes **no assessment** and implies **no medical
 * diagnosis** (NG-03): the copy routes the learner to human help rather than
 * evaluating them. Rendered above the request form so the safe path is the
 * first thing a learner who needs support sees.
 */
export function SafeCounselorPath() {
  const t = useTranslations("wellbeing");
  return (
    <section
      aria-labelledby="safe-path-heading"
      className="flex flex-col gap-2 rounded-md border border-secondary-700/30 bg-primary-50 p-5"
    >
      <h2
        id="safe-path-heading"
        className="text-base font-semibold text-secondary-700"
      >
        {t("counselorHeading")}
      </h2>
      <p className="text-sm text-ink-600">{t("counselorDescription")}</p>
      <p className="text-sm text-ink-600">{t("nonClinicalNote")}</p>
    </section>
  );
}
