"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { FormField } from "@/components/composites/FormField";
import { useCreateSupportRequest } from "@/features/wellbeing/useWellbeing";
import { ApiError } from "@/lib/api/errors";
import {
  supportRequestSchema,
  toSupportRequestPayload,
  type SupportRequestFormValues,
} from "@/features/wellbeing/support-request.schema";

/**
 * Wellbeing support-request form (architecture.md §4, FR-70/FR-71; NL4).
 *
 * A learner who feels they need support writes a short, free-text message; on
 * submit the backend records a routing-only `SupportRequest` and connects them
 * to a counselor (Tier 3). The UI is deliberately **non-clinical**: it makes no
 * assessment, asks for no symptoms/severity, and never implies a medical
 * evaluation (NG-03) — it only opens a safe path to a human. On success it
 * confirms the request was routed and reassures the learner a counselor will
 * reach out.
 *
 * On success the create mutation invalidates the support-requests query so the
 * learner's list re-reads the new request (architecture.md §5.4) — no parent
 * refresh coordination needed.
 */
export function SupportRequestForm() {
  const t = useTranslations("wellbeing");
  const createMutation = useCreateSupportRequest();
  const [status, setStatus] = useState<"idle" | "sent">("idle");
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<SupportRequestFormValues>({
    resolver: zodResolver(supportRequestSchema),
    defaultValues: { message: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    setSubmitError(null);
    try {
      await createMutation.mutateAsync(toSupportRequestPayload(values));
      setStatus("sent");
      reset();
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : t("genericError"));
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {status === "sent" ? (
        <p role="status" className="text-sm text-success-600">
          {t("requestSent")}
        </p>
      ) : null}
      {submitError ? (
        <p role="alert" className="text-sm text-danger-600">
          {submitError}
        </p>
      ) : null}

      <FormField
        id="support-message"
        label={t("messageLabel")}
        hint={t("messageHint")}
        error={errors.message?.message}
      >
        <Textarea rows={5} {...register("message")} />
      </FormField>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting
          ? t("submitting")
          : status === "sent"
            ? t("sendAnother")
            : t("submit")}
      </Button>
    </form>
  );
}
