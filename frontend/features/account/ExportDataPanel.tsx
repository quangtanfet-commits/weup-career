"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { useExportData } from "@/features/account/useAccount";
import { ApiError } from "@/lib/api/errors";
import type { DataExport } from "@/lib/api/endpoints/account";

/**
 * Export-my-data panel (architecture.md §11; FR-92, Law 91/2025 data-subject
 * right of access). Triggers `GET /me/export` on demand and renders the
 * returned JSON for the user to copy, plus a client-side download as a JSON
 * file. The export is a one-shot action, so it is a mutation, not a cached read.
 */
export function ExportDataPanel() {
  const t = useTranslations("account");
  const exportMutation = useExportData();
  const [result, setResult] = useState<DataExport | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const onExport = async () => {
    setSubmitError(null);
    try {
      const data = await exportMutation.mutateAsync();
      setResult(data);
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : t("genericError"));
    }
  };

  const serialized = result ? JSON.stringify(result, null, 2) : "";
  const downloadHref = result
    ? `data:application/json;charset=utf-8,${encodeURIComponent(serialized)}`
    : undefined;

  return (
    <div className="flex flex-col gap-4">
      {submitError ? (
        <p role="alert" className="text-sm text-danger-600">
          {submitError}
        </p>
      ) : null}

      <Button
        type="button"
        onClick={onExport}
        disabled={exportMutation.isPending}
      >
        {exportMutation.isPending
          ? t("data.export.submitting")
          : t("data.export.submit")}
      </Button>

      {result ? (
        <div className="flex flex-col gap-2">
          <p role="status" className="text-sm text-success-600">
            {t("data.export.ready")}
          </p>
          <a
            href={downloadHref}
            download="weup-export.json"
            className="text-sm font-medium text-primary underline"
          >
            {t("data.export.download")}
          </a>
          <pre
            aria-label={t("data.export.previewLabel")}
            className="max-h-72 overflow-auto rounded-md border border-input bg-surface p-3 text-xs text-ink-900"
          >
            {serialized}
          </pre>
        </div>
      ) : null}
    </div>
  );
}
