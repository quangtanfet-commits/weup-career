"use client";

import { use } from "react";
import { notFound, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

import { ConsentGateBanner } from "@/features/consent/ConsentGateBanner";
import { AssessmentRunner } from "@/features/assessments/AssessmentRunner";
import { instrumentNameVi } from "@/features/assessments/instrument-items";
import type { InstrumentType } from "@/lib/api/endpoints/assessments";

const INSTRUMENT_TYPES = new Set<InstrumentType>(["riasec", "vips", "mbti"]);

function isInstrumentType(value: string): value is InstrumentType {
  return INSTRUMENT_TYPES.has(value as InstrumentType);
}

/**
 * Assessment runner route (architecture.md §3 `(app)/assessments/[type]`,
 * FR-10/11). `[gate]`: wrapped in the consent gate (CP-1). An unknown
 * instrument type is a 404 (CP-4 neutral not-found). On submit it routes to the
 * no-cache result view by the new result id (FR-11/15).
 */
export default function AssessmentRunnerPage({
  params,
}: {
  params: Promise<{ type: string }>;
}) {
  const { type } = use(params);
  const t = useTranslations("assessment");
  const router = useRouter();

  if (!isInstrumentType(type)) {
    notFound();
  }

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-bold text-ink-900">
          {instrumentNameVi(type)}
        </h1>
        <p className="mt-2 max-w-2xl text-ink-600">{t("runnerSubtitle")}</p>
      </header>
      <ConsentGateBanner>
        <AssessmentRunner
          instrumentType={type}
          onSubmitted={(resultId) =>
            router.push(`/assessments/results/${resultId}`)
          }
        />
      </ConsentGateBanner>
    </div>
  );
}
