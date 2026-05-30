"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

import { ConsentGateBanner } from "@/features/consent/ConsentGateBanner";
import { ResultView } from "@/features/assessments/ResultView";

/**
 * Sensitive result route (architecture.md §3 `(app)/assessments/results/[id]`,
 * §7 CP-3; FR-11/12/14). `[gate]`: wrapped in the consent gate. The view fetches
 * the result no-cache (each open = one audited read). After a delete it routes
 * back to the instrument list (FR-14).
 */
export default function AssessmentResultPage({
  params,
}: {
  params: Promise<{ resultId: string }>;
}) {
  const { resultId } = use(params);
  const t = useTranslations("assessment");
  const router = useRouter();

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-bold text-ink-900">{t("resultTitle")}</h1>
      </header>
      <ConsentGateBanner>
        <ResultView
          resultId={resultId}
          onDeleted={() => router.push("/assessments")}
        />
      </ConsentGateBanner>
    </div>
  );
}
