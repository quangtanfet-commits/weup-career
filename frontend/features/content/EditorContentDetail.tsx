"use client";

import { useTranslations } from "next-intl";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PublishVersionForm } from "@/features/content/PublishVersionForm";
import { useEditorContentItem } from "@/features/content/useContent";
import { ApiError } from "@/lib/api/errors";

/**
 * Editor content detail (architecture.md §10; FR-90). Reads
 * `GET /content/{id}` (Bearer, R:editor) so the editor sees the item at ANY
 * status (traceability) — the published-only public route would hide a draft.
 * Surfaces the five governance tags and offers the publish-version action.
 *
 * A 404 (item not found / not in the editor's scope) renders a neutral
 * not-found message rather than leaking whether the id exists (CP-4).
 */
export function EditorContentDetail({ contentId }: { contentId: string }) {
  const t = useTranslations("editor");
  const { data, isPending, isError, error } = useEditorContentItem(contentId);

  if (isError) {
    const notFound = error instanceof ApiError && error.status === 404;
    return (
      <p role="alert" className="text-sm text-danger-600">
        {notFound
          ? t("detail.notFound")
          : error instanceof ApiError
            ? error.message
            : t("genericError")}
      </p>
    );
  }

  if (isPending) {
    return (
      <p role="status" className="text-sm text-ink-600">
        {t("detail.loading")}
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>{data.title}</CardTitle>
          <CardDescription>
            {t("detail.statusVersion", {
              status: t(`status.${data.status}`),
              version: data.version,
            })}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <p className="whitespace-pre-wrap text-sm text-ink-900">
            {data.body}
          </p>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs text-ink-600">
            <dt>{t("detail.competency")}</dt>
            <dd className="text-ink-900">{data.competency_code}</dd>
            <dt>{t("detail.dieu5")}</dt>
            <dd className="text-ink-900">{data.dieu5_code}</dd>
            <dt>{t("detail.depth")}</dt>
            <dd className="text-ink-900">
              {data.depth ? t(`depth.${data.depth}`) : "—"}
            </dd>
            <dt>{t("detail.devPhase")}</dt>
            <dd className="text-ink-900">
              {data.dev_phase ? t(`devPhase.${data.dev_phase}`) : "—"}
            </dd>
            <dt>{t("detail.schoolLevel")}</dt>
            <dd className="text-ink-900">
              {data.school_level
                ? t(`schoolLevelOption.${data.school_level}`)
                : "—"}
            </dd>
            <dt>{t("detail.sourceRef")}</dt>
            <dd className="text-ink-900">{data.source_ref || "—"}</dd>
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("publish.title")}</CardTitle>
          <CardDescription>{t("publish.cardDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          <PublishVersionForm contentId={contentId} />
        </CardContent>
      </Card>
    </div>
  );
}
