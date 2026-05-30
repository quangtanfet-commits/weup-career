import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export const metadata: Metadata = { title: "Đăng nhập" };

/**
 * Login route placeholder (architecture.md §3, Luồng 1). The LoginForm
 * (POST /auth/login, RHF + Zod, in-memory token) is implemented in the F1 auth
 * work; F1 foundation ships the route so the `(auth)` group renders.
 */
export default async function LoginPage() {
  const t = await getTranslations("nav");
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("login")}</CardTitle>
        <CardDescription>
          Biểu mẫu đăng nhập sẽ được bổ sung trong slice xác thực F1.
        </CardDescription>
      </CardHeader>
      <CardContent />
    </Card>
  );
}
