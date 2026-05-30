"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";

import { useEditorContentList } from "@/features/content/useContent";
import { ApiError } from "@/lib/api/errors";

/**
 * Editor content list (architecture.md §10; FR-90). Reads `GET /content` WITH
 * the bearer token so it can show items at ANY status (draft/published/
 * archived) — the editor's traceability view, distinct from the public
 * published-only library. Each row links to the editor detail page where a new
 * version can be published. Status is conveyed with text (not colour alone) for
 * a11y (architecture.md §8).
 */
export function ContentList() {
  const t = useTranslations("editor");
  const { data, isPending, isError, error } = useEditorContentList();

  if (isError) {
    return (
      <p role="alert" className="text-sm text-danger-600">
        {error instanceof ApiError ? error.message : t("genericError")}
      </p>
    );
  }

  if (isPending) {
    return (
      <p role="status" className="text-sm text-ink-600">
        {t("list.loading")}
      </p>
    );
  }

  if (data.length === 0) {
    return <p className="text-sm text-ink-600">{t("list.empty")}</p>;
  }

  return (
    <ul className="flex flex-col gap-3">
      {data.map((item) => (
        <li
          key={item.id}
          className="flex flex-col gap-1.5 rounded-md border border-input p-4"
        >
          <div className="flex items-center justify-between gap-3">
            <Link
              href={`/editor/content/${item.id}`}
              className="text-sm font-medium text-secondary-700 underline-offset-2 hover:underline"
            >
              {item.title}
            </Link>
            <span className="rounded-full border border-input px-2 py-0.5 text-xs text-ink-600">
              {t(`status.${item.status}`)}
            </span>
          </div>
          <span className="text-xs text-ink-600">
            {t("list.meta", {
              competency: item.competency_code,
              dieu5: item.dieu5_code,
              version: item.version,
            })}
          </span>
        </li>
      ))}
    </ul>
  );
}
