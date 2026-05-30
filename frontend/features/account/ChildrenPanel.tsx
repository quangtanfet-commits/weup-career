"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/composites/FormField";
import {
  useDeleteChildAccount,
  useExportChildData,
} from "@/features/account/useAccount";
import { ApiError } from "@/lib/api/errors";
import {
  childIdSchema,
  type ChildIdFormValues,
} from "@/features/account/child.schema";
import type { DataExport, DeletionOut } from "@/lib/api/endpoints/account";

/**
 * Guardian per-child data-subject rights (architecture.md §11; FR-92, Law
 * 91/2025). A guardian enters a linked child's id and may export the child's
 * data (`GET /me/children/{id}/export`) or soft-delete the child's account
 * (`DELETE /me/children/{id}`). The destructive action requires an explicit
 * confirm step and surfaces the recovery window. The backend re-checks the
 * guardian link per request (CP-4); this surface is also role-gated to
 * `guardian` by the page.
 */
export function ChildrenPanel() {
  const t = useTranslations("account");
  const exportMutation = useExportChildData();
  const deleteMutation = useDeleteChildAccount();

  const [exportResult, setExportResult] = useState<DataExport | null>(null);
  const [deletionResult, setDeletionResult] = useState<DeletionOut | null>(
    null,
  );
  const [confirming, setConfirming] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    getValues,
    trigger,
    formState: { errors },
  } = useForm<ChildIdFormValues>({
    resolver: zodResolver(childIdSchema),
    defaultValues: { child_id: "" },
  });

  const childId = () => getValues("child_id").trim();

  const onExport = async () => {
    setSubmitError(null);
    setDeletionResult(null);
    if (!(await trigger("child_id"))) return;
    try {
      const data = await exportMutation.mutateAsync(childId());
      setExportResult(data);
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : t("genericError"));
    }
  };

  const onStartDelete = async () => {
    setSubmitError(null);
    if (!(await trigger("child_id"))) return;
    setConfirming(true);
  };

  const onConfirmDelete = async () => {
    setSubmitError(null);
    setExportResult(null);
    try {
      const deletion = await deleteMutation.mutateAsync(childId());
      setDeletionResult(deletion);
      setConfirming(false);
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : t("genericError"));
    }
  };

  const serialized = exportResult ? JSON.stringify(exportResult, null, 2) : "";
  const downloadHref = exportResult
    ? `data:application/json;charset=utf-8,${encodeURIComponent(serialized)}`
    : undefined;

  return (
    <div className="flex flex-col gap-4">
      {submitError ? (
        <p role="alert" className="text-sm text-danger-600">
          {submitError}
        </p>
      ) : null}

      <FormField
        id="child-id"
        label={t("children.childIdLabel")}
        hint={t("children.childIdHint")}
        error={errors.child_id?.message}
      >
        <Input {...register("child_id")} />
      </FormField>

      <div className="flex flex-wrap gap-3">
        <Button
          type="button"
          onClick={onExport}
          disabled={exportMutation.isPending}
        >
          {exportMutation.isPending
            ? t("children.export.submitting")
            : t("children.export.submit")}
        </Button>
        {!confirming ? (
          <Button type="button" variant="danger" onClick={onStartDelete}>
            {t("children.delete.start")}
          </Button>
        ) : null}
      </div>

      {confirming ? (
        <div className="flex flex-col gap-3 rounded-md border border-danger-600 p-4">
          <p className="text-sm font-medium text-ink-900">
            {t("children.delete.confirmPrompt")}
          </p>
          <div className="flex flex-wrap gap-3">
            <Button
              type="button"
              variant="danger"
              onClick={onConfirmDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending
                ? t("children.delete.submitting")
                : t("children.delete.confirm")}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setConfirming(false)}
              disabled={deleteMutation.isPending}
            >
              {t("children.delete.cancel")}
            </Button>
          </div>
        </div>
      ) : null}

      {deletionResult ? (
        <div role="status" className="flex flex-col gap-2">
          <p className="text-sm font-medium text-ink-900">
            {t("children.delete.done")}
          </p>
          <p className="text-sm text-ink-600">
            {t("children.delete.recoveryWindow", {
              days: deletionResult.recovery_window_days,
            })}
          </p>
          <p className="text-sm text-ink-600">
            {t("children.delete.purgeDue", {
              date: new Date(deletionResult.purge_due_at).toLocaleDateString(
                "vi-VN",
              ),
            })}
          </p>
        </div>
      ) : null}

      {exportResult ? (
        <div className="flex flex-col gap-2">
          <p role="status" className="text-sm text-success-600">
            {t("children.export.ready")}
          </p>
          <a
            href={downloadHref}
            download="weup-child-export.json"
            className="text-sm font-medium text-primary underline"
          >
            {t("children.export.download")}
          </a>
          <pre
            aria-label={t("children.export.previewLabel")}
            className="max-h-72 overflow-auto rounded-md border border-input bg-surface p-3 text-xs text-ink-900"
          >
            {serialized}
          </pre>
        </div>
      ) : null}
    </div>
  );
}
