"use client";

import { use } from "react";
import Link from "next/link";
import { useTranslations } from "next-intl";

import { EditorContentDetail } from "@/features/content/EditorContentDetail";

/**
 * Content-editor detail route (architecture.md §3 `(app)/editor/content/[id]`,
 * FR-90). Gated to `content_editor` by the segment layout. Views the item at
 * ALL statuses via `GET /content/{id}` and publishes a new version via
 * `POST /content/{id}/versions`.
 */
export default function EditorContentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const t = useTranslations("editor");

  return (
    <div className="flex flex-col gap-6">
      <Link
        href="/editor/content"
        className="text-sm text-secondary-700 underline-offset-2 hover:underline"
      >
        {t("detail.back")}
      </Link>
      <EditorContentDetail contentId={id} />
    </div>
  );
}
