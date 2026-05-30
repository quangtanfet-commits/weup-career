"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { FormField } from "@/components/composites/FormField";
import { useAssignMember } from "@/features/school/useSchool";
import { ApiError } from "@/lib/api/errors";
import {
  ASSIGNABLE_ROLES,
  assignMemberSchema,
  toAssignMemberPayload,
  type AssignMemberFormValues,
} from "@/features/school/assign-member.schema";

/**
 * Assign-member form (architecture.md §4, §10; FR-80). A `school_admin` assigns
 * a user as a `student` or `counselor` in the school, optionally scoped to a
 * class. The role options mirror the backend's assignable roles (no
 * `school_admin`); the backend re-checks scope per request (CP-4). On success
 * the school's class list is invalidated by the mutation hook.
 */
export function AssignMemberForm({ schoolId }: { schoolId: string }) {
  const t = useTranslations("schoolAdmin");
  const assignMutation = useAssignMember(schoolId);
  const [status, setStatus] = useState<"idle" | "assigned">("idle");
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<AssignMemberFormValues>({
    resolver: zodResolver(assignMemberSchema),
    defaultValues: { user_id: "", role: "student", class_id: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    setSubmitError(null);
    try {
      await assignMutation.mutateAsync(toAssignMemberPayload(values));
      setStatus("assigned");
      reset();
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : t("genericError"));
    }
  });

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {status === "assigned" ? (
        <p role="status" className="text-sm text-success-600">
          {t("assignMember.assigned")}
        </p>
      ) : null}
      {submitError ? (
        <p role="alert" className="text-sm text-danger-600">
          {submitError}
        </p>
      ) : null}

      <FormField
        id="member-user-id"
        label={t("assignMember.userIdLabel")}
        hint={t("assignMember.userIdHint")}
        error={errors.user_id?.message}
      >
        <Input {...register("user_id")} />
      </FormField>

      <FormField
        id="member-role"
        label={t("assignMember.roleLabel")}
        error={errors.role?.message}
      >
        <Select {...register("role")}>
          {ASSIGNABLE_ROLES.map((role) => (
            <option key={role} value={role}>
              {t(`assignMember.roleOption.${role}`)}
            </option>
          ))}
        </Select>
      </FormField>

      <FormField
        id="member-class-id"
        label={t("assignMember.classIdLabel")}
        hint={t("assignMember.classIdHint")}
        error={errors.class_id?.message}
      >
        <Input {...register("class_id")} />
      </FormField>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? t("assignMember.submitting") : t("assignMember.submit")}
      </Button>
    </form>
  );
}
