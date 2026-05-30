"use client";

import { use } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { DeSensitizedStudentView } from "@/features/counseling/DeSensitizedStudentView";
import { useStudentProgress } from "@/features/counseling/useCounseling";
import { ApiError } from "@/lib/api/errors";

/**
 * One student's de-sensitized view (architecture.md §3, §4.4, §7; FR-82,
 * CP-3/CP-4). Role-gated by `(app)/counselor/layout.tsx`. Reads GET
 * `/school/students/{student_id}/progress`, which returns ONLY de-sensitized
 * data (no raw assessment payload, CP-3).
 *
 * CP-4: a 404 (not assigned / [CRED_2DA28CFA] access) is shown as a NEUTRAL not-found state
 * — it never reveals whether the student exists or whether access was denied.
 */
export default function CounselorStudentPage({
  params,
}: {
  params: Promise<{ studentId: string }>;
}) {
  const { studentId } = use(params);
  const t = useTranslations("counselor");
  const common = useTranslations("common");

  const progress = useStudentProgress(studentId);

  const isNotFound =
    progress.error instanceof ApiError &&
    (progress.error.status === 404 || progress.error.status === 403);

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-2">
        <Link
          href="/counselor/students"
          className="text-sm text-secondary-700 underline-offset-2 hover:underline"
        >
          {t("backToRoster")}
        </Link>
        <h1 className="text-2xl font-bold text-ink-900">{t("studentTitle")}</h1>
      </header>

      {progress.isLoading ? (
        <p role="status" className="text-sm text-ink-600">
          {t("studentLoading")}
        </p>
      ) : isNotFound ? (
        <div
          role="status"
          className="mx-auto mt-6 max-w-lg rounded-md border border-input bg-surface p-6 text-center"
        >
          <p className="text-base font-semibold text-ink-900">
            {t("notFoundTitle")}
          </p>
          <p className="mt-2 text-sm text-ink-600">{t("notFoundNeutral")}</p>
        </div>
      ) : progress.isError ? (
        <div
          role="alert"
          className="flex flex-col items-start gap-3 rounded-md border border-danger-600/40 bg-danger-600/10 p-5"
        >
          <p className="text-sm text-danger-600">{t("studentLoadError")}</p>
          <Button variant="outline" onClick={() => void progress.refetch()}>
            {common("retry")}
          </Button>
        </div>
      ) : progress.data ? (
        <DeSensitizedStudentView data={progress.data} />
      ) : null}
    </div>
  );
}
