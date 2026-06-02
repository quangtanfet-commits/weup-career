"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";

export type VerifyState = "verifying" | "success" | "invalid";

export interface VerifyEmailViewProps {
  state: VerifyState;
}

/**
 * Presentational view for the email-verification result
 * (email-verification-2026-06.md §3.2). Pure props so Storybook can render every
 * state without a network round-trip; the side-effecting POST lives in
 * `VerifyEmailClient`. `invalid` never distinguishes wrong / expired / consumed)
 * (matches the backend's generic 401) and points the user at /login, where the
 * resend affordance lives.
 */
export function VerifyEmailView({ state }: VerifyEmailViewProps) {
  const t = useTranslations("auth");

  if (state === "verifying") {
    return (
      <p role="status" aria-busy="true" className="text-sm text-ink-700">
        {t("verifying")}
      </p>
    );
  }

  if (state === "success") {
    return (
      <div className="flex flex-col gap-4">
        <h2 className="text-lg font-semibold text-ink-900">
          {t("verifySuccessTitle")}
        </h2>
        <p role="status" className="text-sm text-ink-700">
          {t("verifySuccessBody")}
        </p>
        <Button asChild>
          <Link href="/login">{t("goLoginCta")}</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-ink-900">
        {t("verifyInvalidTitle")}
      </h2>
      <p role="alert" className="text-sm text-danger-600">
        {t("verifyInvalidBody")}
      </p>
      <Button asChild variant="outline">
        <Link href="/login">{t("goLoginCta")}</Link>
      </Button>
    </div>
  );
}
