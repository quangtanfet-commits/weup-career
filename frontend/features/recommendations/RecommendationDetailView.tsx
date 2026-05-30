"use client";

import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/errors";
import { RecommendationCard } from "./RecommendationCard";
import { useRecommendation } from "./useRecommendations";

/**
 * F5 single-recommendation page body (architecture.md §3
 * `(app)/recommendations/[recoId]`, §10 L5; FR-61/62, CP-5/CP-6).
 *
 * Accessible to the owner, a linked guardian, or an assigned counselor; the
 * backend returns 404 for anyone else (existence-hiding, CP-4) which we surface
 * as a neutral not-found state — never revealing whether the id exists. On a
 * successful read the `RecommendationCard` renders the payload, the MANDATORY
 * rationale (CP-6) and the explicit human-confirm cluster (CP-5).
 *
 * This route is intentionally NOT consent-gated (architecture.md §3 — no
 * `[gate]` marker): a guardian/counselor confirming on a learner's behalf is a
 * legitimate human-in-the-loop path, and read access is already authorised
 * server-side by relation.
 */
export function RecommendationDetailView({ recoId }: { recoId: string }) {
  const t = useTranslations("recommendations");
  const common = useTranslations("common");
  const query = useRecommendation(recoId);

  if (query.isLoading) {
    return (
      <p role="status" className="text-sm text-ink-600">
        {t("detailLoading")}
      </p>
    );
  }

  // `isError` (or the rare resolved-but-undefined) falls through to the error
  // state; a 404 (no access / not found) gets the neutral not-found copy.
  if (query.isError || query.data === undefined) {
    const notFound =
      query.error instanceof ApiError && query.error.status === 404;
    return (
      <div
        role="alert"
        className="flex flex-col items-start gap-3 rounded-md border border-danger-600/40 bg-danger-600/10 p-5"
      >
        <p className="text-sm text-danger-600">
          {notFound ? t("detailNotFound") : t("detailLoadError")}
        </p>
        {notFound ? null : (
          <Button variant="outline" onClick={() => void query.refetch()}>
            {common("retry")}
          </Button>
        )}
      </div>
    );
  }

  return <RecommendationCard recommendation={query.data} />;
}
