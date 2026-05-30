"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { RosterTable } from "@/features/counseling/RosterTable";
import { useSchoolStudents } from "@/features/counseling/useCounseling";
import { ApiError } from "@/lib/api/errors";

/**
 * Reads the `?school=` query and renders the de-sensitized roster. Split out so
 * the `useSearchParams()` call sits inside a Suspense boundary (Next.js 15
 * requirement; mirrors the RSC static-prerender guidance).
 *
 * `school_id` is DB-relational (not on the user object), so it is read from the
 * query param. When absent, a neutral prompt is shown rather than guessing.
 * CP-4: a 403/404 (not a member / [CRED_DA1B4D11] authorised) is rendered as a NEUTRAL
 * not-found state — it never reveals whether the school/roster exists.
 */
function RosterSection() {
  const t = useTranslations("counselor");
  const common = useTranslations("common");
  const searchParams = useSearchParams();
  const schoolId = searchParams.get("school");

  const roster = useSchoolStudents(schoolId);

  const entries = roster.data ?? [];
  const isNotFound =
    roster.error instanceof ApiError &&
    (roster.error.status === 404 || roster.error.status === 403);

  if (schoolId === null || schoolId === "") {
    return <p className="text-sm text-ink-600">{t("rosterNeedsSchool")}</p>;
  }
  if (roster.isLoading) {
    return (
      <p role="status" className="text-sm text-ink-600">
        {t("rosterLoading")}
      </p>
    );
  }
  if (isNotFound) {
    return <p className="text-sm text-ink-600">{t("notFoundNeutral")}</p>;
  }
  if (roster.isError) {
    return (
      <div
        role="alert"
        className="flex flex-col items-start gap-3 rounded-md border border-danger-600/40 bg-danger-600/10 p-5"
      >
        <p className="text-sm text-danger-600">{t("rosterLoadError")}</p>
        <Button variant="outline" onClick={() => void roster.refetch()}>
          {common("retry")}
        </Button>
      </div>
    );
  }
  if (entries.length === 0) {
    return <p className="text-sm text-ink-600">{t("rosterEmpty")}</p>;
  }
  return <RosterTable entries={entries} />;
}

/**
 * Counselor roster route (architecture.md §3, §6.2; FR-82, CP-3/CP-4).
 * Role-gated by `(app)/counselor/layout.tsx`. The de-sensitized roster comes
 * from GET `/school/{school_id}/students`.
 */
export default function CounselorStudentsPage() {
  const t = useTranslations("counselor");

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-ink-900">{t("rosterTitle")}</h1>
        <p className="text-sm text-ink-600">{t("rosterSubtitle")}</p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>{t("rosterCardTitle")}</CardTitle>
          <CardDescription>{t("rosterCardDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          <Suspense fallback={null}>
            <RosterSection />
          </Suspense>
        </CardContent>
      </Card>
    </div>
  );
}
