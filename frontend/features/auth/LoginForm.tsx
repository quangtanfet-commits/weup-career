"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/composites/FormField";
import { login } from "@/lib/api/endpoints/auth";
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
 */
export function LoginForm({ redirectTo = "/dashboard" }: { redirectTo?: string }) {
  const t = useTranslations("auth");
  const router = useRouter();
  const setSessionFromToken = useAuthStore((s) => s.setSessionFromToken);
  const [submitError, setSubmitError] = useState<string | null>(null);

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
    try {
      const res = await login(toLoginPayload(values));
      setSessionFromToken(res.access_token, res.user);
      router.replace(redirectTo);
    } catch (err) {
      setSubmitError(
        err instanceof ApiError ? err.message : t("genericError"),
      );
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {submitError ? (
        <p role="alert" className="text-sm text-danger-600">
          {submitError}
        </p>
      ) : null}

      <FormField id="login-email" label={t("email")} error={errors.email?.message}>
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
