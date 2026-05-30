"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ConsentGateBanner } from "@/features/consent/ConsentGateBanner";
import { SafeCounselorPath } from "@/features/wellbeing/SafeCounselorPath";
import { SupportRequestForm } from "@/features/wellbeing/SupportRequestForm";
import { SupportRequestList } from "@/features/wellbeing/SupportRequestList";

/**
 * Wellbeing route (architecture.md §3, §10; FR-70/FR-71, NL4) — the smallest
 * `[gate]` slice. Client-rendered inside the authenticated `(app)` group so
 * personal data is fetched with the in-memory bearer token (never the RSC
 * cache). For a child <16 without active guardian consent, `ConsentGateBanner`
 * soft-blocks the data-creating area (CP-1) while keeping the supportive
 * intro/safe-path copy visible.
 *
 * The page is deliberately **non-clinical** (NG-03): it offers stress/balance
 * guidance and a safe path to a human counselor (Tier 3); it never diagnoses or
 * implies a medical assessment. A local `refreshKey` re-loads the request list
 * after a new request is created.
 */
export default function WellbeingPage() {
  const t = useTranslations("wellbeing");
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("pageTitle")}</CardTitle>
          <CardDescription>{t("pageDescription")}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <p className="text-sm text-ink-600">{t("introStress")}</p>
          <p className="text-sm text-ink-600">{t("introBalance")}</p>
          <p className="text-sm text-ink-600">{t("introSeekHelp")}</p>
        </CardContent>
      </Card>

      <SafeCounselorPath />

      <ConsentGateBanner>
        <Card>
          <CardHeader>
            <CardTitle>{t("requestTitle")}</CardTitle>
            <CardDescription>{t("requestDescription")}</CardDescription>
          </CardHeader>
          <CardContent>
            <SupportRequestForm onCreated={() => setRefreshKey((k) => k + 1)} />
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle>{t("listTitle")}</CardTitle>
            <CardDescription>{t("listDescription")}</CardDescription>
          </CardHeader>
          <CardContent>
            <SupportRequestList refreshKey={refreshKey} />
          </CardContent>
        </Card>
      </ConsentGateBanner>
    </div>
  );
}
