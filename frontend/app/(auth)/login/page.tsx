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
import { LoginForm } from "@/features/auth/LoginForm";

export const metadata: Metadata = { title: "Đăng nhập" };

/**
 * Login route (architecture.md §3, Luồng 1; CP-7). Server-rendered card chrome
 * wraps the client `LoginForm` (POST /auth/login, RHF + Zod, in-memory token).
 */
export default async function LoginPage() {
  const t = await getTranslations("auth");
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("loginTitle")}</CardTitle>
        <CardDescription>{t("loginDescription")}</CardDescription>
      </CardHeader>
      <CardContent>
        <LoginForm />
      </CardContent>
      <CardFooter className="justify-center gap-1 text-sm text-ink-600">
        <span>{t("noAccount")}</span>
        <Link href="/register" className="font-medium text-primary-700">
          {t("goRegister")}
        </Link>
      </CardFooter>
    </Card>
  );
}
