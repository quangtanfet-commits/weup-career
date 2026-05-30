"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ContentList } from "@/features/content/ContentList";
import { CreateContentForm } from "@/features/content/CreateContentForm";

/**
 * Content-editor index route (architecture.md §3, §10; FR-90). Gated to
 * `content_editor` by the segment layout. Lists `GET /content` WITH the bearer
 * token (all statuses, editor traceability) and creates a draft via
 * `POST /content`. A local `refreshKey` re-renders the list after a draft is
 * created (the mutation also invalidates the query cache).
 */
export default function EditorContentPage() {
  const t = useTranslations("editor");
  const [, setRefreshKey] = useState(0);

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("list.pageTitle")}</CardTitle>
          <CardDescription>{t("list.pageDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          <ContentList />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("createContent.title")}</CardTitle>
          <CardDescription>{t("createContent.description")}</CardDescription>
        </CardHeader>
        <CardContent>
          <CreateContentForm onCreated={() => setRefreshKey((k) => k + 1)} />
        </CardContent>
      </Card>
    </div>
  );
}
