import type { Metadata } from "next";
import Link from "next/link";
import { getTranslations } from "next-intl/server";

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { RegisterForm } from "@/features/auth/RegisterForm";

export const metadata: Metadata = { title: "Đăng ký" };

/**
 * Registration route (architecture.md §3, Luồng 1; CP-1). Server-rendered card
 * chrome wraps the client `RegisterForm`, which surfaces the guardian-consent
 * path for under-16 registrants and routes to `/consent` when the backend marks
 * the account `pending_guardian_consent`.
 */
export default async function RegisterPage() {
  const t = await getTranslations("auth");
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("registerTitle")}</CardTitle>
        <CardDescription>{t("registerDescription")}</CardDescription>
      </CardHeader>
      <CardContent>
        <RegisterForm />
      </CardContent>
      <CardFooter className="justify-center gap-1 text-sm text-ink-600">
        <span>{t("haveAccount")}</span>
        <Link href="/login" className="font-medium text-primary-700">
          {t("goLogin")}
        </Link>
      </CardFooter>
    </Card>
  );
}
