"use client";

import { use } from "react";
import { useTranslations } from "next-intl";

import { RecommendationDetailView } from "@/features/recommendations/RecommendationDetailView";

/**
 * Single-recommendation route (architecture.md §3
 * `(app)/recommendations/[recoId]`, §10 L5; FR-61/62, CP-5/CP-6). Client-
 * rendered inside the guarded `(app)` group so the personal recommendation is
 * fetched with the in-memory bearer token (never the RSC cache,
 * architecture.md §5.4). The view shows the card with its mandatory rationale
 * (CP-6) and the explicit human-confirm cluster (CP-5).
 */
export default function RecommendationDetailPage({
  params,
}: {
  params: Promise<{ recoId: string }>;
}) {
  const { recoId } = use(params);
  const t = useTranslations("recommendations");

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-bold text-ink-900">{t("detailTitle")}</h1>
      </header>
      <RecommendationDetailView recoId={recoId} />
    </div>
  );
}
