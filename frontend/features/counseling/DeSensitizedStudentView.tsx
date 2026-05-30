"use client";

import { useTranslations } from "next-intl";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type {
  StudentProgressOut,
  CounselorProgressItemOut,
  DesensitizedAssessmentOut,
} from "@/lib/api/endpoints/counseling";

/**
 * A counselor's de-sensitized view of one student (architecture.md §4.4; FR-82,
 * CP-3/CP-4). It renders ONLY the de-sensitized `StudentProgressOut` shape:
 *
 *  - competency progress: area + competency name + achieved depth (K/A/R) and
 *    development phase — derived, non-sensitive coordinates;
 *  - assessments: instrument type + derived summary code ONLY — never the raw
 *    answers/result payload.
 *
 * A persistent banner makes the de-sensitization explicit so the counselor
 * understands they are not seeing private assessment data (CP-3).
 */
export function DeSensitizedStudentView({
  data,
}: {
  data: StudentProgressOut;
}) {
  const t = useTranslations("counselor");
  const tp = useTranslations("progress");

  const progress: readonly CounselorProgressItemOut[] = data.progress;
  const assessments: readonly DesensitizedAssessmentOut[] = data.assessments;

  return (
    <div className="flex flex-col gap-6">
      <div
        role="note"
        data-desensitized="true"
        className="rounded-md border border-secondary-700/30 bg-primary-50 p-4 text-sm text-secondary-700"
      >
        {t("desensitizedNote")}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("studentProgressHeading")}</CardTitle>
          <CardDescription>{t("studentProgressDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          {progress.length === 0 ? (
            <p className="text-sm text-ink-600">{t("studentProgressEmpty")}</p>
          ) : (
            <ul className="flex flex-col gap-3">
              {progress.map((item) => (
                <li
                  key={item.competency_id}
                  className="flex flex-col gap-1 rounded-md border border-input p-3"
                >
                  <span className="text-xs uppercase tracking-wide text-ink-600">
                    {tp(`area.${item.area}`)}
                  </span>
                  <span className="text-sm font-medium text-ink-900">
                    {item.name_vi}
                  </span>
                  <span className="text-sm text-ink-600">
                    {t("currentDepthLabel")}:{" "}
                    {item.depth_achieved
                      ? tp(`depth.${item.depth_achieved}`)
                      : tp("noProgressYet")}
                    {" · "}
                    {t("devPhaseLabel")}: {tp(`devPhase.${item.dev_phase}`)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("assessmentsHeading")}</CardTitle>
          <CardDescription>{t("assessmentsDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          {assessments.length === 0 ? (
            <p className="text-sm text-ink-600">{t("assessmentsEmpty")}</p>
          ) : (
            <ul className="flex flex-col gap-2">
              {assessments.map((item, index) => (
                <li
                  key={`${item.instrument_type}-${index}`}
                  className="flex items-center justify-between gap-3 rounded-md border border-input px-3 py-2"
                >
                  <span className="text-sm font-medium text-ink-900">
                    {item.instrument_type}
                  </span>
                  <span className="text-sm text-ink-600">
                    {item.summary_code ?? t("noSummaryCode")}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
