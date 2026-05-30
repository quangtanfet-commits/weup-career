"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { usePublishContentVersion } from "@/features/content/useContent";
import { ApiError } from "@/lib/api/errors";

/**
 * Publish-version action (architecture.md §10; FR-90). Promotes a content
 * item's current draft state to the next published version via
 * `POST /content/{id}/versions` (no request body — the backend archives the
 * prior published version). On success the mutation hook invalidates the item +
 * lists so the new version/status is re-read from the backend.
 */
export function PublishVersionForm({ contentId }: { contentId: string }) {
  const t = useTranslations("editor");
  const publishMutation = usePublishContentVersion(contentId);
  const [status, setStatus] = useState<"idle" | "published">("idle");
  const [submitError, setSubmitError] = useState<string | null>(null);

  const onPublish = async () => {
    setSubmitError(null);
    try {
      await publishMutation.mutateAsync();
      setStatus("published");
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : t("genericError"));
    }
  };

  return (
    <div className="flex flex-col gap-3">
      {status === "published" ? (
        <p role="status" className="text-sm text-success-600">
          {t("publish.published")}
        </p>
      ) : null}
      {submitError ? (
        <p role="alert" className="text-sm text-danger-600">
          {submitError}
        </p>
      ) : null}

      <p className="text-sm text-ink-600">{t("publish.description")}</p>

      <Button
        type="button"
        onClick={() => void onPublish()}
        disabled={publishMutation.isPending}
      >
        {publishMutation.isPending
          ? t("publish.submitting")
          : t("publish.submit")}
      </Button>
    </div>
  );
}
