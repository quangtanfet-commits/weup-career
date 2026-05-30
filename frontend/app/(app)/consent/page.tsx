"use client";

import { useTranslations } from "next-intl";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { GuardianInviteForm } from "@/features/consent/GuardianInviteForm";

/**
 * Guardian-consent route (architecture.md §4.4, FR-03; CP-1/CP-2). A child <16
 * lands here after registration (account `pending_guardian_consent`) to invite a
 * guardian by email. Client-rendered (inside the guarded `(app)` group) so it
 * reads the in-memory session and never leaks PII into the RSC cache.
 */
export default function ConsentPage() {
  const t = useTranslations("consent");
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("pageTitle")}</CardTitle>
        <CardDescription>{t("pageDescription")}</CardDescription>
      </CardHeader>
      <CardContent>
        <GuardianInviteForm />
      </CardContent>
    </Card>
  );
}
