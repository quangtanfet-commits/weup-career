"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/composites/FormField";
import { useChangePassword } from "@/features/account/useAccount";
import { ApiError } from "@/lib/api/errors";
import {
  changePasswordSchema,
  toPasswordChangePayload,
  type ChangePasswordFormValues,
} from "@/features/account/password.schema";

/**
 * Change-password form (architecture.md §11; FR-91). Requires the current
 * password to authorise, plus a confirmation of the new one (client-side
 * guard). The backend returns 204 on success; the form surfaces a status line
 * and clears the inputs. The backend remains the authority on the password
 * policy and on verifying the current secret.
 */
export function ChangePasswordForm() {
  const t = useTranslations("account");
  const changeMutation = useChangePassword();
  const [status, setStatus] = useState<"idle" | "changed">("idle");
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ChangePasswordFormValues>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      current_password: "",
      new_password: "",
      confirm_password: "",
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    setSubmitError(null);
    setStatus("idle");
    try {
      await changeMutation.mutateAsync(toPasswordChangePayload(values));
      setStatus("changed");
      reset();
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : t("genericError"));
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {status === "changed" ? (
        <p role="status" className="text-sm text-success-600">
          {t("security.changed")}
        </p>
      ) : null}
      {submitError ? (
        <p role="alert" className="text-sm text-danger-600">
          {submitError}
        </p>
      ) : null}

      <FormField
        id="current-password"
        label={t("security.currentLabel")}
        error={errors.current_password?.message}
      >
        <Input type="password" autoComplete="current-password" {...register("current_password")} />
      </FormField>

      <FormField
        id="new-password"
        label={t("security.newLabel")}
        hint={t("security.newHint")}
        error={errors.new_password?.message}
      >
        <Input type="password" autoComplete="new-password" {...register("new_password")} />
      </FormField>

      <FormField
        id="confirm-password"
        label={t("security.confirmLabel")}
        error={errors.confirm_password?.message}
      >
        <Input type="password" autoComplete="new-password" {...register("confirm_password")} />
      </FormField>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? t("security.submitting") : t("security.submit")}
      </Button>
    </form>
  );
}
