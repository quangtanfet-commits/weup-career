"use client";

import { useTranslations } from "next-intl";

import { ConsentGateBanner } from "@/features/consent/ConsentGateBanner";
import { InstrumentList } from "@/features/assessments/InstrumentList";

/**
 * Assessment instrument list (architecture.md §3 `(app)/assessments`, FR-10).
 * Client-rendered inside the guarded `(app)` group and wrapped in the consent
 * gate: a child <16 without active consent sees the soft gate instead of the
 * list (CP-1). The backend stays the final authority.
 */
export default function AssessmentsPage() {
  const t = useTranslations("assessment");
  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-3xl font-bold text-ink-900">{t("listTitle")}</h1>
        <p className="mt-2 max-w-2xl text-ink-600">{t("listSubtitle")}</p>
      </header>
      <ConsentGateBanner>
        <InstrumentList />
      </ConsentGateBanner>
    </div>
  );
}
