import { getTranslations } from "next-intl/server";

import type { ContentItem } from "@/lib/api/endpoints/content";

/**
 * Public content view (architecture.md §3 — `(public)/content/[contentId]`).
 * Renders a published `ContentItemOut` (Điều 5(a)/(c)/(d)). All prose is
 * server-versioned content from the backend; the FE only lays it out (§9).
 */
export async function ContentView({ item }: { item: ContentItem }) {
  const t = await getTranslations("content");
  const schoolLevel = await getTranslations("schoolLevel");

  return (
    <article className="mt-6 flex flex-col gap-6">
      <header className="flex flex-col gap-3">
        <h1 className="text-3xl font-bold text-ink-900">{item.title}</h1>
        <dl className="flex flex-wrap gap-x-8 gap-y-2 text-sm">
          <div className="flex gap-2">
            <dt className="font-medium text-ink-600">{t("dieu5Label")}:</dt>
            <dd className="text-ink-900">{item.dieu5_code}</dd>
          </div>
          <div className="flex gap-2">
            <dt className="font-medium text-ink-600">
              {t("competencyLabel")}:
            </dt>
            <dd className="text-ink-900">{item.competency_code}</dd>
          </div>
          {item.school_level ? (
            <div className="flex gap-2">
              <dt className="font-medium text-ink-600">
                {t("schoolLevelLabel")}:
              </dt>
              <dd className="text-ink-900">{schoolLevel(item.school_level)}</dd>
            </div>
          ) : null}
        </dl>
      </header>

      <div className="whitespace-pre-line leading-relaxed text-ink-900">
        {item.body}
      </div>
    </article>
  );
}
