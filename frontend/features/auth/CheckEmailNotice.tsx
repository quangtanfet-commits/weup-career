"use client";

import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";

export type ResendState = "idle" | "resending" | "done";

export interface CheckEmailNoticeProps {
  email: string;
  resendState: ResendState;
  onResend: () => void;
}

/**
 * Post-register "check your email" notice (email-verification-2026-06.md §3.1).
 * Pure presentational: the parent owns the resend network call and passes the
 * `resendState` down, so the component is Storybook-able without a backend. The
 * copy is identical for new / duplicate / under-16 emails — no enumeration oracle.
 */
export function CheckEmailNotice({
  email,
  resendState,
  onResend,
}: CheckEmailNoticeProps) {
  const t = useTranslations("auth");
  const resending = resendState === "resending";

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold text-ink-900">
        {t("checkEmailTitle")}
      </h2>
      <p role="status" className="text-sm text-ink-700">
        {t("checkEmailBody", { email })}
      </p>

      {resendState === "done" ? (
        <p role="status" className="text-sm text-success-700">
          {t("resendDone")}
        </p>
      ) : null}

      <Button
        type="button"
        variant="outline"
        onClick={onResend}
        disabled={resending}
        aria-disabled={resending}
      >
        {resending ? t("submitting") : t("resend")}
      </Button>
    </div>
  );
}
