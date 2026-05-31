"use client";

import { useTranslations } from "next-intl";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ExportDataPanel } from "@/features/account/ExportDataPanel";
import { DeleteAccountPanel } from "@/features/account/DeleteAccountPanel";

/**
 * Data-subject-rights route (architecture.md §11; FR-92, Law 91/2025). Lets the
 * logged-in user export their data (`GET /me/export`) and request soft-deletion
 * of their account (`DELETE /me`, with an explicit recovery window).
 */
export default function AccountDataPage() {
  const t = useTranslations("account");
  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("data.export.pageTitle")}</CardTitle>
          <CardDescription>{t("data.export.pageDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          <ExportDataPanel />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("data.delete.pageTitle")}</CardTitle>
          <CardDescription>{t("data.delete.pageDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          <DeleteAccountPanel />
        </CardContent>
      </Card>
    </div>
  );
}
