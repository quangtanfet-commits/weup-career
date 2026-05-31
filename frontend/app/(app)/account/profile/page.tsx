"use client";

import { useTranslations } from "next-intl";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ProfileForm } from "@/features/account/ProfileForm";

/**
 * Profile route (architecture.md §11; FR-91). Authed (the `(app)` layout
 * guards it). Reads `GET /me/profile` and updates the SAFE fields via
 * `PATCH /me`.
 */
export default function AccountProfilePage() {
  const t = useTranslations("account");
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("profile.pageTitle")}</CardTitle>
        <CardDescription>{t("profile.pageDescription")}</CardDescription>
      </CardHeader>
      <CardContent>
        <ProfileForm />
      </CardContent>
    </Card>
  );
}
