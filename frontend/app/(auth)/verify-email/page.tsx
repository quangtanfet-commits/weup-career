import type { Metadata } from "next";
import { Suspense } from "react";
import { getTranslations } from "next-intl/server";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { VerifyEmailClient } from "@/features/auth/VerifyEmailClient";

export const metadata: Metadata = { title: "Xác minh email" };

/**
 * Email-verification route (email-verification-2026-06.md §3.2). Server-rendered
 * card chrome wraps the client `VerifyEmailClient`, which reads `?token=` and
 * POSTs it to /auth/verify-email. The Suspense boundary is required because the
 * client uses `useSearchParams`; it also keeps the token out of any static
 * prerender.
 */
export default async function VerifyEmailPage() {
  const t = await getTranslations("auth");
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("verifyTitle")}</CardTitle>
      </CardHeader>
      <CardContent>
        <Suspense fallback={null}>
          <VerifyEmailClient />
        </Suspense>
      </CardContent>
    </Card>
  );
}
