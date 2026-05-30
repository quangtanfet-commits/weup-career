import type { Metadata } from "next";
import Link from "next/link";
import { getTranslations } from "next-intl/server";

import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { listContent, type ContentItem } from "@/lib/api/endpoints/content";

/**
 * Public content library (Điều 5(a)/(c)/(d)) — supports the
 * `(public)/content/[contentId]` detail route by making published items
 * discoverable. A **React Server Component**: fetches `GET /api/v1/content`
 * anonymously server-side (published-only, BE-1; no token — §5.4).
 */
export const metadata: Metadata = {
  title: "Nội dung hướng nghiệp",
  description:
    "Tài liệu hướng nghiệp công khai theo Điều 5 — không cần đăng nhập.",
};

const MAX_VISIBLE = 120;

// The frontend image is built without a reachable backend, so a page that
// fetches backend data must render at request time — otherwise Next.js bakes an
// empty list into the static output at `docker build` and serves it forever.
// The careers page is already dynamic (it reads `searchParams`); this page has
// no such input, so force dynamic rendering explicitly. (`publicFetch` keeps its
// own revalidate cache, so this does not disable data caching.)
export const dynamic = "force-dynamic";

export default async function ContentLibraryPage() {
  const t = await getTranslations("content");

  let items: ContentItem[] = [];
  let failed = false;
  try {
    items = await listContent();
  } catch {
    failed = true;
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-12">
      <h1 className="text-3xl font-bold text-ink-900">{t("title")}</h1>
      <p className="mt-2 max-w-2xl text-ink-600">{t("subtitle")}</p>

      {failed ? (
        <p role="alert" className="mt-8 text-danger-600">
          {t("loadError")}
        </p>
      ) : items.length === 0 ? (
        <p className="mt-8 text-ink-600">{t("empty")}</p>
      ) : (
        <ul className="mt-8 grid gap-4 sm:grid-cols-2">
          {items.slice(0, MAX_VISIBLE).map((item) => (
            <li key={item.id}>
              <Card className="h-full transition-shadow hover:shadow-md">
                <CardHeader>
                  <CardTitle>
                    <Link
                      href={`/content/${encodeURIComponent(item.id)}`}
                      className="text-ink-900 hover:text-primary-700 focus-visible:underline focus-visible:outline-none"
                    >
                      {item.title}
                    </Link>
                  </CardTitle>
                  <p className="text-sm text-ink-600">
                    {t("dieu5Label")} {item.dieu5_code} · {item.competency_code}
                  </p>
                </CardHeader>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
