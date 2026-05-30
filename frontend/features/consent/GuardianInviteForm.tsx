"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { FormField } from "@/components/composites/FormField";
import { inviteGuardian } from "@/lib/api/endpoints/guardians";
import { ApiError } from "@/lib/api/errors";
import {
  guardianInviteSchema,
  relationships,
  toGuardianInvitePayload,
  type GuardianInviteFormValues,
} from "@/features/consent/guardian-invite.schema";

const RELATIONSHIP_LABELS: Record<(typeof relationships)[number], string> = {
  mother: "Mẹ",
  father: "Bố",
  guardian: "Người giám hộ khác",
};

/**
 * Guardian-invite form (architecture.md §4.4, FR-03; CP-1). A child <16 invites
 * a guardian by email so the guardian can verify the link and grant consent.
 * `onInvited` lets the parent page refresh the consent status after a successful
 * invite/resend.
 */
export function GuardianInviteForm({
  onInvited,
}: {
  onInvited?: () => void;
}) {
  const t = useTranslations("consent");
  const [status, setStatus] = useState<"idle" | "sent">("idle");
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<GuardianInviteFormValues>({
    resolver: zodResolver(guardianInviteSchema),
    defaultValues: { guardian_email: "", relationship: "mother" },
  });

  const onSubmit = handleSubmit(async (values) => {
    setSubmitError(null);
    try {
      await inviteGuardian(toGuardianInvitePayload(values));
      setStatus("sent");
      reset();
      onInvited?.();
    } catch (err) {
      setSubmitError(
        err instanceof ApiError ? err.message : t("genericError"),
      );
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {status === "sent" ? (
        <p role="status" className="text-sm text-success-600">
          {t("inviteSent")}
        </p>
      ) : null}
      {submitError ? (
        <p role="alert" className="text-sm text-danger-600">
          {submitError}
        </p>
      ) : null}

      <FormField
        id="guardian-email"
        label={t("guardianEmail")}
        error={errors.guardian_email?.message}
      >
        <Input
          type="email"
          autoComplete="email"
          {...register("guardian_email")}
        />
      </FormField>

      <FormField
        id="guardian-relationship"
        label={t("relationship")}
        error={errors.relationship?.message}
      >
        <Select {...register("relationship")}>
          {relationships.map((value) => (
            <option key={value} value={value}>
              {RELATIONSHIP_LABELS[value]}
            </option>
          ))}
        </Select>
      </FormField>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting
          ? t("submitting")
          : status === "sent"
            ? t("resend")
            : t("sendInvite")}
      </Button>
    </form>
  );
}
