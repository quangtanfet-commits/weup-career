"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { FormField } from "@/components/composites/FormField";
import { useCreateCounselingSession } from "@/features/counseling/useCounseling";
import type { CounselingTier } from "@/lib/api/endpoints/counseling";
import { ApiError } from "@/lib/api/errors";
import {
  counselingSessionSchema,
  toCreateSessionPayload,
  type CounselingSessionFormValues,
} from "@/features/counseling/session.schema";

const TIERS: readonly CounselingTier[] = ["1", "2", "3"];

/**
 * Log a counseling session (architecture.md §4.4, §6.2; FR-81). The counselor
 * records which student they supported and at which of the three tiers
 * (Tier 1 universal / [CRED_84287963] 2 group / [CRED_C40FC2F4] 3 individual), with optional notes.
 *
 * On submit the backend creates a `CounselingSession` (POST
 * `/counseling/sessions`) and stamps `counselor_id` from the authenticated
 * principal. `student_id` is a free text field by default so a session can be
 * logged from anywhere; the optional `defaultStudentId` pre-fills it when the
 * counselor arrives from a student's view.
 */
export function SessionForm({
  defaultStudentId = "",
}: {
  defaultStudentId?: string;
}) {
  const t = useTranslations("counselor");
  const [status, setStatus] = useState<"idle" | "sent">("idle");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const createSession = useCreateCounselingSession();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CounselingSessionFormValues>({
    resolver: zodResolver(counselingSessionSchema),
    defaultValues: { student_id: defaultStudentId, tier: "3", notes: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    setSubmitError(null);
    try {
      await createSession.mutateAsync(toCreateSessionPayload(values));
      setStatus("sent");
      reset({ student_id: defaultStudentId, tier: "3", notes: "" });
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : t("genericError"));
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {status === "sent" ? (
        <p role="status" className="text-sm text-success-600">
          {t("sessionSaved")}
        </p>
      ) : null}
      {submitError ? (
        <p role="alert" className="text-sm text-danger-600">
          {submitError}
        </p>
      ) : null}

      <FormField
        id="session-student-id"
        label={t("sessionStudentLabel")}
        hint={t("sessionStudentHint")}
        error={errors.student_id?.message}
      >
        <Input {...register("student_id")} />
      </FormField>

      <FormField
        id="session-tier"
        label={t("sessionTierLabel")}
        hint={t("sessionTierHint")}
        error={errors.tier?.message}
      >
        <Select {...register("tier")}>
          {TIERS.map((tier) => (
            <option key={tier} value={tier}>
              {t(`tier.${tier}`)}
            </option>
          ))}
        </Select>
      </FormField>

      <FormField
        id="session-notes"
        label={t("sessionNotesLabel")}
        hint={t("sessionNotesHint")}
        error={errors.notes?.message}
      >
        <Textarea rows={5} {...register("notes")} />
      </FormField>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting
          ? t("sessionSubmitting")
          : status === "sent"
            ? t("sessionLogAnother")
            : t("sessionSubmit")}
      </Button>
    </form>
  );
}
