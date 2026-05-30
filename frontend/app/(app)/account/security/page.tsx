"use client";

import { useTranslations } from "next-intl";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ChangePasswordForm } from "@/features/account/ChangePasswordForm";

/**
 * Security route (architecture.md §11; FR-91). Change password via
 * `POST /me/password` (requires the current password).
 */
export default function AccountSecurityPage() {
  const t = useTranslations("account");
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("security.pageTitle")}</CardTitle>
        <CardDescription>{t("security.pageDescription")}</CardDescription>
      </CardHeader>
      <CardContent>
        <ChangePasswordForm />
      </CardContent>
    </Card>
  );
}
