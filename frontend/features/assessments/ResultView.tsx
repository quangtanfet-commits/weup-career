"use client";

import { useState } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  deleteResult,
  getResult,
  type ResultDetailOut,
} from "@/lib/api/endpoints/assessments";
import { ApiError } from "@/lib/api/errors";
import { useSensitiveQuery } from "@/lib/query/sensitive";
import { SensitiveBadge } from "@/features/assessments/SensitiveBadge";
import { interpretResult } from "@/features/assessments/instrument-items";
import type { InstrumentType } from "@/lib/api/endpoints/assessments";

/**
 * ResultView (architecture.md §4.4, §7 CP-3; FR-12/14). Renders a sensitive
 * `AssessmentResult`:
 *  - fetched with `useSensitiveQuery` (no cache, no persist) so each view is a
 *    fresh audited backend read (CP-3);
 *  - headed by `SensitiveBadge` + an "ai xem được?" panel;
 *  - presented as an **explanation + career groups to explore**, never a hard
 *    "you must do job X" verdict (FR-12);
 *  - with **export** (download the result the learner is already viewing) and
 *    **delete** (data-subject rights, FR-14) controls.
 */
export interface ResultViewProps {
  readonly resultId: string;
  /** Called after a successful delete so the page can route away (FR-14). */
  readonly onDeleted?: () => void;
}

/** Read the payload `type` defensively, defaulting to riasec interpretation. */
function payloadType(payload: Record<string, unknown>): InstrumentType {
  const t = payload.type;
  if (t === "riasec" || t === "vips" || t === "mbti") return t;
  return "riasec";
}

function downloadResult(result: ResultDetailOut) {
  const blob = new Blob([JSON.stringify(result, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `assessment-result-${result.id}.json`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function ResultView({ resultId, onDeleted }: ResultViewProps) {
  const t = useTranslations("assessment");
  const { data, isLoading, isError, error } =
    useSensitiveQuery<ResultDetailOut>(["assessment-result", resultId], () =>
      getResult(resultId),
    );

  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  async function onDelete() {
    setActionError(null);
    setDeleting(true);
    try {
      await deleteResult(resultId);
      onDeleted?.();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : t("deleteError"));
      setDeleting(false);
    }
  }

  if (isLoading) {
    return (
      <p role="status" className="text-sm text-ink-600">
        {t("loadingResult")}
      </p>
    );
  }

  if (isError || !data) {
    const message =
      error instanceof ApiError ? error.message : t("loadResultError");
    return (
      <p role="alert" className="text-sm text-danger-600">
        {message}
      </p>
    );
  }

  const type = payloadType(data.payload);
  const interpreted = interpretResult(type, data.payload);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center gap-3">
        <SensitiveBadge />
        <span className="text-xs text-ink-600">
          {t("resultVersion", { version: data.version })}
        </span>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("resultTitle")}</CardTitle>
          <CardDescription>{t("resultExplanation")}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-5">
          {interpreted.code ? (
            <p className="text-sm text-ink-900">
              {t("resultCode")}{" "}
              <span className="font-semibold text-primary-700">
                {interpreted.code}
              </span>
            </p>
          ) : null}

          {interpreted.scores.length > 0 ? (
            <div>
              <h3 className="text-sm font-semibold text-ink-900">
                {t("scoresHeading")}
              </h3>
              <ul className="mt-2 flex flex-col gap-1.5">
                {interpreted.scores.map(([label, score]) => (
                  <li
                    key={label}
                    className="flex items-center justify-between gap-3 text-sm text-ink-600"
                  >
                    <span>{label}</span>
                    <span className="font-medium text-ink-900">{score}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {interpreted.careerGroups.length > 0 ? (
            <div>
              <h3 className="text-sm font-semibold text-ink-900">
                {t("careerGroupsHeading")}
              </h3>
              <p className="mt-1 text-xs text-ink-600">
                {t("careerGroupsHint")}
              </p>
              <ul className="mt-2 flex flex-wrap gap-2">
                {interpreted.careerGroups.map((group) => (
                  <li key={group.code}>
                    <Link
                      href={group.href}
                      className="inline-flex rounded-full border border-primary-600/30 bg-primary-50 px-3 py-1 text-sm text-primary-700 hover:bg-primary-50/70"
                    >
                      {group.label_vi}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {/* FR-12: never a hard verdict — the decision stays with the human. */}
          <p
            role="note"
            className="rounded-md border border-warning-600/30 bg-warning-600/10 p-3 text-sm text-ink-600"
          >
            {t("noHardVerdict")}
          </p>
        </CardContent>
      </Card>

      <section
        aria-label={t("whoCanSeeHeading")}
        className="rounded-md border border-sensitive-700/30 bg-sensitive-700/5 p-4"
      >
        <h3 className="text-sm font-semibold text-sensitive-700">
          {t("whoCanSeeHeading")}
        </h3>
        <p className="mt-1 text-sm text-ink-600">{t("whoCanSeeBody")}</p>
      </section>

      {actionError ? (
        <p role="alert" className="text-sm text-danger-600">
          {actionError}
        </p>
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        <Button
          type="button"
          variant="outline"
          onClick={() => downloadResult(data)}
        >
          {t("exportResult")}
        </Button>

        {confirmDelete ? (
          <>
            <Button
              type="button"
              variant="danger"
              onClick={onDelete}
              disabled={deleting}
            >
              {deleting ? t("deleting") : t("confirmDelete")}
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={() => setConfirmDelete(false)}
              disabled={deleting}
            >
              {t("cancelDelete")}
            </Button>
          </>
        ) : (
          <Button
            type="button"
            variant="danger"
            onClick={() => setConfirmDelete(true)}
          >
            {t("deleteResult")}
          </Button>
        )}
      </div>
    </div>
  );
}
