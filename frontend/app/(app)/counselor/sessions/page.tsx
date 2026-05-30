"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { SessionForm } from "@/features/counseling/SessionForm";

/**
 * Reads the `?student=` query and renders the form. Split out so the
 * `useSearchParams()` call sits inside a Suspense boundary (Next.js 15
 * requirement; mirrors the RSC static-prerender guidance).
 */
function SessionFormSection() {
  const searchParams = useSearchParams();
  const defaultStudentId = searchParams.get("student") ?? "";
  return <SessionForm defaultStudentId={defaultStudentId} />;
}

/**
 * Log a counseling session (architecture.md §3, §6.2; FR-81). Role-gated by
 * `(app)/counselor/layout.tsx`. Renders the `SessionForm`, which POSTs to
 * `/counseling/sessions`. An optional `?student=` query pre-fills the student
 * when the counselor arrives from a student's de-sensitized view.
 */
export default function CounselorSessionsPage() {
  const t = useTranslations("counselor");

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-ink-900">{t("sessionTitle")}</h1>
        <p className="text-sm text-ink-600">{t("sessionSubtitle")}</p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>{t("sessionCardTitle")}</CardTitle>
          <CardDescription>{t("sessionCardDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          <Suspense fallback={null}>
            <SessionFormSection />
          </Suspense>
        </CardContent>
      </Card>
    </div>
  );
}
