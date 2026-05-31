"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { FormField } from "@/components/composites/FormField";
import { useProfile, useUpdateProfile } from "@/features/account/useAccount";
import { ApiError } from "@/lib/api/errors";
import {
  SCHOOL_LEVELS,
  USER_TYPES,
  profileUpdateSchema,
  toProfileUpdatePayload,
  type ProfileFormValues,
} from "@/features/account/profile.schema";

/**
 * Profile view + edit (architecture.md §11; FR-91). Reads `GET /me/profile`,
 * shows the read-only identity fields (email, age band — not editable, they
 * gate consent/ownership), and lets the user PATCH the SAFE editable fields
 * (`school_level`, `user_type`) via `PATCH /me`. The selects pre-fill from the
 * loaded profile so an edit is a deliberate change, not a blind overwrite.
 */
export function ProfileForm() {
  const t = useTranslations("account");
  const { data, isPending, isError, error } = useProfile();
  const updateMutation = useUpdateProfile();
  const [status, setStatus] = useState<"idle" | "saved">("idle");
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileUpdateSchema),
    defaultValues: { school_level: "none", user_type: "student" },
  });

  // Pre-fill the editable selects once the profile resolves.
  useEffect(() => {
    if (data) {
      reset({ school_level: data.school_level, user_type: data.user_type });
    }
  }, [data, reset]);

  if (isError) {
    return (
      <p role="alert" className="text-sm text-danger-600">
        {error instanceof ApiError ? error.message : t("genericError")}
      </p>
    );
  }

  if (isPending) {
    return (
      <p role="status" className="text-sm text-ink-600">
        {t("profile.loading")}
      </p>
    );
  }

  const onSubmit = handleSubmit(async (values) => {
    setSubmitError(null);
    setStatus("idle");
    try {
      await updateMutation.mutateAsync(toProfileUpdatePayload(values));
      setStatus("saved");
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : t("genericError"));
    }
  });

  return (
    <div className="flex flex-col gap-6">
      <dl className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <dt className="text-xs text-ink-600">{t("profile.emailLabel")}</dt>
          <dd className="text-sm font-medium text-ink-900">{data.email}</dd>
        </div>
        <div>
          <dt className="text-xs text-ink-600">{t("profile.ageBandLabel")}</dt>
          <dd className="text-sm font-medium text-ink-900">
            {t(`ageBand.${data.age_band}`)}
          </dd>
        </div>
      </dl>

      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        {status === "saved" ? (
          <p role="status" className="text-sm text-success-600">
            {t("profile.saved")}
          </p>
        ) : null}
        {submitError ? (
          <p role="alert" className="text-sm text-danger-600">
            {submitError}
          </p>
        ) : null}

        <FormField
          id="profile-school-level"
          label={t("profile.schoolLevelLabel")}
          error={errors.school_level?.message}
        >
          <Select {...register("school_level")}>
            {SCHOOL_LEVELS.map((level) => (
              <option key={level} value={level}>
                {t(`schoolLevelOption.${level}`)}
              </option>
            ))}
          </Select>
        </FormField>

        <FormField
          id="profile-user-type"
          label={t("profile.userTypeLabel")}
          error={errors.user_type?.message}
        >
          <Select {...register("user_type")}>
            {USER_TYPES.map((type) => (
              <option key={type} value={type}>
                {t(`userTypeOption.${type}`)}
              </option>
            ))}
          </Select>
        </FormField>

        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? t("profile.submitting") : t("profile.submit")}
        </Button>
      </form>
    </div>
  );
}
