"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/lib/auth/store";
import { isConsentGated } from "@/lib/auth/consent";

/**
 * Soft consent gate (architecture.md §4.4, §7 CP-1/CP-2). Wraps `[gate]`
 * features: when the signed-in user is a child <16 without active guardian
 * consent, it renders a non-dismissable notice + CTA to `/consent` instead of
 * the feature, so the user is never led into a backend 403 dead end. When not
 * gated it renders its children unchanged. Public content is never wrapped.
 */
export function ConsentGateBanner({ children }: { children: React.ReactNode }) {
  const t = useTranslations("consent");
  const user = useAuthStore((s) => s.user);

  if (!isConsentGated(user)) {
    return <>{children}</>;
  }

  return (
    <section
      role="status"
      aria-live="polite"
      className="flex flex-col gap-3 rounded-md border border-warning-600/40 bg-warning-600/10 p-5"
    >
      <h2 className="text-base font-semibold text-warning-600">
        {t("gateTitle")}
      </h2>
      <p className="text-sm text-ink-600">{t("gateDescription")}</p>
      <div>
        <Button asChild>
          <Link href="/consent">{t("gateCta")}</Link>
        </Button>
      </div>
    </section>
  );
}
