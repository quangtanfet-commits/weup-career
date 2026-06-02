"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/composites/FormField";
import { type ResendState } from "@/features/auth/CheckEmailNotice";
import { login, resendVerification } from "@/lib/api/endpoints/auth";
import { ApiError } from "@/lib/api/errors";
import { useAuthStore } from "@/lib/auth/store";
import {
  loginSchema,
  toLoginPayload,
  type LoginFormValues,
} from "@/features/auth/login.schema";

/**
 * Login form (architecture.md §3, Luồng 1; CP-7). RHF + Zod validates client
 * side, `POST /auth/login` sets the httpOnly refresh cookie and returns the
 * access token + user, which is stored **in memory only** (no localStorage).
 *
 * Post-N-3 (email-verification-2026-06.md §3.3): a correct password on an
 * unverified account returns `403 EMAIL_NOT_VERIFIED` — shown as a *distinct*
 * not-verified message with a resend affordance (prefilled with the entered
 * email), separate from the generic 401. Account-status routing
 * (`pending_guardian_consent → /consent`) moved here from RegisterForm because it
 * can only run once a verified session exists.
 */
export function LoginForm({
  redirectTo = "/dashboard",
}: {
  redirectTo?: string;
}) {
  const t = useTranslations("auth");
  const router = useRouter();
  const setSessionFromToken = useAuthStore((s) => s.setSessionFromToken);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [notVerifiedEmail, setNotVerifiedEmail] = useState<string | null>(null);
  const [resendState, setResendState] = useState<ResendState>("idle");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    setSubmitError(null);
    setNotVerifiedEmail(null);
    setResendState("idle");
    try {
      const res = await login(toLoginPayload(values));
      setSessionFromToken(res.access_token, res.user);
      const next =
        res.user.account_status === "pending_guardian_consent"
          ? "/consent"
          : redirectTo;
      router.replace(next);
    } catch (err) {
      if (err instanceof ApiError && err.code === "EMAIL_NOT_VERIFIED") {
        setNotVerifiedEmail(values.email);
        return;
      }
      setSubmitError(err instanceof ApiError ? err.message : t("genericError"));
    }
  });

  async function handleResend() {
    if (!notVerifiedEmail || resendState === "resending") return;
    setResendState("resending");
    try {
      await resendVerification(notVerifiedEmail);
    } finally {
      setResendState("done");
    }
  }

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {submitError ? (
        <p role="alert" className="text-sm text-danger-600">
          {submitError}
        </p>
      ) : null}

      {notVerifiedEmail ? (
        <div role="alert" className="flex flex-col gap-2 text-sm">
          <p className="text-danger-600">{t("emailNotVerified")}</p>
          {resendState === "done" ? (
            <p role="status" className="text-success-700">
              {t("resendDone")}
            </p>
          ) : (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleResend}
              disabled={resendState === "resending"}
              aria-disabled={resendState === "resending"}
            >
              {resendState === "resending" ? t("submitting") : t("resend")}
            </Button>
          )}
        </div>
      ) : null}

      <FormField
        id="login-email"
        label={t("email")}
        error={errors.email?.message}
      >
        <Input type="email" autoComplete="email" {...register("email")} />
      </FormField>

      <FormField
        id="login-password"
        label={t("password")}
        error={errors.password?.message}
      >
        <Input
          type="password"
          autoComplete="current-password"
          {...register("password")}
        />
      </FormField>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? t("submitting") : t("loginSubmit")}
      </Button>
    </form>
  );
}
