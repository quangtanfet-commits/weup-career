"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { useDeleteAccount } from "@/features/account/useAccount";
import { ApiError } from "@/lib/api/errors";
import type { DeletionOut } from "@/lib/api/endpoints/account";

/**
 * Delete-my-account panel (architecture.md §11; FR-92, Law 91/2025 right to
 * erasure). Deletion is a SOFT delete with a recovery window, so the UI: (1)
 * requires an explicit confirm step before firing `DELETE /me`, and (2) on
 * success surfaces the recovery window EXPLICITLY (days + the purge-due date
 * from `DeletionOut`) so the user knows the account can be recovered until then.
 */
export function DeleteAccountPanel() {
  const t = useTranslations("account");
  const deleteMutation = useDeleteAccount();
  const [confirming, setConfirming] = useState(false);
  const [result, setResult] = useState<DeletionOut | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const onConfirmDelete = async () => {
    setSubmitError(null);
    try {
      const deletion = await deleteMutation.mutateAsync();
      setResult(deletion);
      setConfirming(false);
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : t("genericError"));
    }
  };

  if (result) {
    return (
      <div role="status" className="flex flex-col gap-2">
        <p className="text-sm font-medium text-ink-900">
          {t("data.delete.done")}
        </p>
        <p className="text-sm text-ink-600">
          {t("data.delete.recoveryWindow", {
            days: result.recovery_window_days,
          })}
        </p>
        <p className="text-sm text-ink-600">
          {t("data.delete.purgeDue", {
            date: new Date(result.purge_due_at).toLocaleDateString("vi-VN"),
          })}
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      {submitError ? (
        <p role="alert" className="text-sm text-danger-600">
          {submitError}
        </p>
      ) : null}

      <p className="text-sm text-ink-600">{t("data.delete.description")}</p>

      {confirming ? (
        <div className="flex flex-col gap-3 rounded-md border border-danger-600 p-4">
          <p className="text-sm font-medium text-ink-900">
            {t("data.delete.confirmPrompt")}
          </p>
          <div className="flex flex-wrap gap-3">
            <Button
              type="button"
              variant="danger"
              onClick={onConfirmDelete}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending
                ? t("data.delete.submitting")
                : t("data.delete.confirm")}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => setConfirming(false)}
              disabled={deleteMutation.isPending}
            >
              {t("data.delete.cancel")}
            </Button>
          </div>
        </div>
      ) : (
        <Button
          type="button"
          variant="danger"
          onClick={() => setConfirming(true)}
        >
          {t("data.delete.start")}
        </Button>
      )}
    </div>
  );
}
