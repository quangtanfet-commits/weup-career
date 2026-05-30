"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/composites/FormField";
import { useCreateClass } from "@/features/school/useSchool";
import { ApiError } from "@/lib/api/errors";
import {
  createClassSchema,
  toCreateClassPayload,
  type CreateClassFormValues,
} from "@/features/school/create-class.schema";

/**
 * Create-class form (architecture.md §4, §10; FR-80). A `school_admin` names a
 * class and tags its grade; on success the school's class list is invalidated
 * by the mutation hook so it re-reads the new row from the backend. The form is
 * disabled until a `schoolId` is known (the page collects it first).
 */
export function CreateClassForm({ schoolId }: { schoolId: string }) {
  const t = useTranslations("schoolAdmin");
  const createMutation = useCreateClass(schoolId);
  const [status, setStatus] = useState<"idle" | "created">("idle");
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateClassFormValues>({
    resolver: zodResolver(createClassSchema),
    defaultValues: { name: "", grade: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    setSubmitError(null);
    try {
      await createMutation.mutateAsync(toCreateClassPayload(values));
      setStatus("created");
      reset();
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : t("genericError"));
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {status === "created" ? (
        <p role="status" className="text-sm text-success-600">
          {t("createClass.created")}
        </p>
      ) : null}
      {submitError ? (
        <p role="alert" className="text-sm text-danger-600">
          {submitError}
        </p>
      ) : null}

      <FormField
        id="class-name"
        label={t("createClass.nameLabel")}
        error={errors.name?.message}
      >
        <Input {...register("name")} />
      </FormField>

      <FormField
        id="class-grade"
        label={t("createClass.gradeLabel")}
        hint={t("createClass.gradeHint")}
        error={errors.grade?.message}
      >
        <Input {...register("grade")} />
      </FormField>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? t("createClass.submitting") : t("createClass.submit")}
      </Button>
    </form>
  );
}
