import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { ContentView } from "@/features/content/ContentView";
import {
  getPublicContentItem,
  type ContentItem,
} from "@/lib/api/endpoints/content";

/**
 * Public content detail (Điều 5(a)/(c)/(d)) — architecture.md §3
 * `(public)/content/[contentId]`.
 *
 * **React Server Component**: resolves the item from the anonymous published
 * list (`GET /api/v1/content`; there is no anonymous `GET /content/{id}` — that
 * route is editor-only, §6.2). An unknown/unpublished id renders the neutral
 * not-found page.
 */
type PageProps = { params: Promise<{ contentId: string }> };

async function loadContent(contentId: string): Promise<ContentItem | null> {
  return getPublicContentItem(contentId);
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { contentId } = await params;
  const item = await loadContent(contentId);
  if (!item) return { title: "Không tìm thấy nội dung" };
  return { title: item.title, description: item.body.slice(0, 160) };
}

export default async function ContentDetailPage({ params }: PageProps) {
  const { contentId } = await params;
  const t = await getTranslations("content");
  const item = await loadContent(contentId);

  if (!item) notFound();

  // Await the async child Server Component so the full tree resolves in one
  // pass (composition; also keeps the page unit-testable).
  const viewNode = await ContentView({ item });

  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <Link
        href="/content"
        className="text-sm font-medium text-primary-700 hover:underline"
      >
        ← {t("backToList")}
      </Link>
      {viewNode}
    </main>
  );
}
