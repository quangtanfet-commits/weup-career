"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { FormField } from "@/components/composites/FormField";
import { login, register as registerAccount } from "@/lib/api/endpoints/auth";
import { ApiError } from "@/lib/api/errors";
import { useAuthStore } from "@/lib/auth/store";
import {
  registerSchema,
  requiresGuardian,
  schoolLevels,
  toRegisterPayload,
  userTypes,
  type RegisterFormValues,
} from "@/features/auth/register.schema";

const SCHOOL_LEVEL_LABELS: Record<(typeof schoolLevels)[number], string> = {
  primary: "Tiểu học",
  lower_secondary: "THCS",
  upper_secondary: "THPT",
  tertiary: "Cao đẳng / Đại học",
  none: "Khác / Không áp dụng",
};

const USER_TYPE_LABELS: Record<(typeof userTypes)[number], string> = {
  student: "Học sinh",
  working: "Người đi làm",
};

/**
 * Registration form (architecture.md §3, Luồng 1; CP-1). RHF + Zod mirrors the
 * backend rules. When the date of birth implies a child <16, a guardian-consent
 * notice is shown (legal basis: under-16 register via a guardian). On success
 * the user is logged in and routed to `/consent` if the backend marks the
 * account `pending_guardian_consent`, otherwise to the dashboard.
 */
export function RegisterForm() {
  const t = useTranslations("auth");
  const router = useRouter();
  const setSessionFromToken = useAuthStore((s) => s.setSessionFromToken);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
      password: "",
      confirmPassword: "",
      date_of_birth: "",
      school_level: "lower_secondary",
      user_type: "student",
    },
  });

  // react-hook-form's `watch()` returns a non-memoizable function, so React
  // Compiler skips memoizing this component — inherent to the library, not a
  // defect. See docs/frontend/migrations/next-16.md § React Compiler rules.
  // eslint-disable-next-line react-hooks/incompatible-library
  const dob = watch("date_of_birth");
  const showGuardianNotice = dob ? requiresGuardian(dob) : false;

  const onSubmit = handleSubmit(async (values) => {
    setSubmitError(null);
    try {
      await registerAccount(toRegisterPayload(values));
      // Register returns no token; log in to obtain the session.
      const res = await login({
        email: values.email,
        password: values.password,
      });
      setSessionFromToken(res.access_token, res.user);
      const next =
        res.user.account_status === "pending_guardian_consent"
          ? "/consent"
          : "/dashboard";
      router.replace(next);
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : t("genericError"));
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {submitError ? (
        <p role="alert" className="text-sm text-danger-600">
          {submitError}
        </p>
      ) : null}

      <FormField
        id="register-email"
        label={t("email")}
        error={errors.email?.message}
      >
        <Input type="email" autoComplete="email" {...register("email")} />
      </FormField>

      <FormField
        id="register-dob"
        label={t("dateOfBirth")}
        error={errors.date_of_birth?.message}
        hint={t("dateOfBirthHint")}
      >
        <Input type="date" autoComplete="bday" {...register("date_of_birth")} />
      </FormField>

      {showGuardianNotice ? (
        <p
          role="status"
          className="rounded-sm border border-warning-600/40 bg-warning-600/10 p-3 text-sm text-warning-600"
        >
          {t("guardianNotice")}
        </p>
      ) : null}

      <FormField
        id="register-user-type"
        label={t("userType")}
        error={errors.user_type?.message}
      >
        <Select {...register("user_type")}>
          {userTypes.map((value) => (
            <option key={value} value={value}>
              {USER_TYPE_LABELS[value]}
            </option>
          ))}
        </Select>
      </FormField>

      <FormField
        id="register-school-level"
        label={t("schoolLevel")}
        error={errors.school_level?.message}
      >
        <Select {...register("school_level")}>
          {schoolLevels.map((value) => (
            <option key={value} value={value}>
              {SCHOOL_LEVEL_LABELS[value]}
            </option>
          ))}
        </Select>
      </FormField>

      <FormField
        id="register-password"
        label={t("password")}
        error={errors.password?.message}
        hint={t("passwordHint")}
      >
        <Input
          type="password"
          autoComplete="new-password"
          {...register("password")}
        />
      </FormField>

      <FormField
        id="register-confirm-password"
        label={t("confirmPassword")}
        error={errors.confirmPassword?.message}
      >
        <Input
          type="password"
          autoComplete="new-password"
          {...register("confirmPassword")}
        />
      </FormField>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? t("submitting") : t("registerSubmit")}
      </Button>
    </form>
  );
}
