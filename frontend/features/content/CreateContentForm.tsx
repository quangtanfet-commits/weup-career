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
import { useCreateContent } from "@/features/content/useContent";
import { ApiError } from "@/lib/api/errors";
import {
  DEPTH_VALUES,
  DEV_PHASE_VALUES,
  SCHOOL_LEVEL_VALUES,
  createContentSchema,
  toCreateContentPayload,
  type CreateContentFormValues,
} from "@/features/content/create-content.schema";

/**
 * Create-content draft form (architecture.md §4, §10; FR-90). A
 * `content_editor` drafts a content unit with the five mandatory tags
 * (competency_code, dieu5_code, depth, dev_phase, school_level) the backend
 * requires. On success the editor lists are invalidated by the mutation hook so
 * the new draft appears. `onCreated` lets the parent refresh/scroll if needed.
 */
export function CreateContentForm({ onCreated }: { onCreated?: () => void }) {
  const t = useTranslations("editor");
  const createMutation = useCreateContent();
  const [status, setStatus] = useState<"idle" | "created">("idle");
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateContentFormValues>({
    resolver: zodResolver(createContentSchema),
    defaultValues: {
      title: "",
      body: "",
      competency_code: "",
      dieu5_code: "",
      depth: "K",
      dev_phase: "awareness",
      school_level: "lower_secondary",
      source_ref: "",
    },
  });

  const onSubmit = handleSubmit(async (values) => {
    setSubmitError(null);
    try {
      await createMutation.mutateAsync(toCreateContentPayload(values));
      setStatus("created");
      reset();
      onCreated?.();
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : t("genericError"));
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {status === "created" ? (
        <p role="status" className="text-sm text-success-600">
          {t("createContent.created")}
        </p>
      ) : null}
      {submitError ? (
        <p role="alert" className="text-sm text-danger-600">
          {submitError}
        </p>
      ) : null}

      <FormField
        id="content-title"
        label={t("createContent.titleLabel")}
        error={errors.title?.message}
      >
        <Input {...register("title")} />
      </FormField>

      <FormField
        id="content-body"
        label={t("createContent.bodyLabel")}
        error={errors.body?.message}
      >
        <Textarea rows={5} {...register("body")} />
      </FormField>

      <FormField
        id="content-competency"
        label={t("createContent.competencyLabel")}
        hint={t("createContent.competencyHint")}
        error={errors.competency_code?.message}
      >
        <Input {...register("competency_code")} />
      </FormField>

      <FormField
        id="content-dieu5"
        label={t("createContent.dieu5Label")}
        hint={t("createContent.dieu5Hint")}
        error={errors.dieu5_code?.message}
      >
        <Input {...register("dieu5_code")} />
      </FormField>

      <FormField
        id="content-depth"
        label={t("createContent.depthLabel")}
        error={errors.depth?.message}
      >
        <Select {...register("depth")}>
          {DEPTH_VALUES.map((v) => (
            <option key={v} value={v}>
              {t(`depth.${v}`)}
            </option>
          ))}
        </Select>
      </FormField>

      <FormField
        id="content-dev-phase"
        label={t("createContent.devPhaseLabel")}
        error={errors.dev_phase?.message}
      >
        <Select {...register("dev_phase")}>
          {DEV_PHASE_VALUES.map((v) => (
            <option key={v} value={v}>
              {t(`devPhase.${v}`)}
            </option>
          ))}
        </Select>
      </FormField>

      <FormField
        id="content-school-level"
        label={t("createContent.schoolLevelLabel")}
        error={errors.school_level?.message}
      >
        <Select {...register("school_level")}>
          {SCHOOL_LEVEL_VALUES.map((v) => (
            <option key={v} value={v}>
              {t(`schoolLevelOption.${v}`)}
            </option>
          ))}
        </Select>
      </FormField>

      <FormField
        id="content-source-ref"
        label={t("createContent.sourceRefLabel")}
        hint={t("createContent.sourceRefHint")}
        error={errors.source_ref?.message}
      >
        <Input {...register("source_ref")} />
      </FormField>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting
          ? t("createContent.submitting")
          : t("createContent.submit")}
      </Button>
    </form>
  );
}
