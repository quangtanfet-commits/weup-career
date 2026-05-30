"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ConsentGateBanner } from "@/features/consent/ConsentGateBanner";
import { ApiError } from "@/lib/api/errors";
import { useGenerateRecommendation } from "./useRecommendations";

/**
 * F5 recommendations list/entry page body (architecture.md §3
 * `(app)/recommendations`, §10 L5; FR-60..62, CP-5/CP-6). `[gate]`: the
 * data-creating area is wrapped in `ConsentGateBanner` so a child <16 without
 * active guardian consent is soft-blocked before any backend 403 (CP-1).
 *
 * The backend exposes no "list" endpoint (architecture.md §6.2 `reco`): only
 * generate (POST), read-by-id, and confirm. So this page is the generate entry
 * point — it explains the human-in-the-loop rule (CP-5) and, on a successful
 * generate, routes to the recommendation's detail page where the mandatory
 * rationale (CP-6) and the explicit confirm cluster (CP-5) live. There is no
 * auto-apply: generating only *produces* a suggestion, it never enacts it.
 */
export function RecommendationsView() {
  const t = useTranslations("recommendations");
  const router = useRouter();
  const generate = useGenerateRecommendation();
  const [error, setError] = useState<string | null>(null);

  const onGenerate = () => {
    setError(null);
    generate.mutate(undefined, {
      onSuccess: (reco) => {
        router.push(`/recommendations/${reco.id}`);
      },
      onError: (err) => {
        setError(err instanceof ApiError ? err.message : t("genericError"));
      },
    });
  };

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-ink-900">{t("listTitle")}</h1>
        <p className="text-sm text-ink-600">{t("listSubtitle")}</p>
      </header>

      <ConsentGateBanner>
        <Card>
          <CardHeader>
            <CardTitle>{t("generateTitle")}</CardTitle>
            <CardDescription>{t("generateDescription")}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="text-sm text-ink-600">{t("humanInLoopNotice")}</p>
            {error ? (
              <p role="alert" className="text-sm text-danger-600">
                {error}
              </p>
            ) : null}
            <div>
              <Button
                type="button"
                onClick={onGenerate}
                disabled={generate.isPending}
              >
                {generate.isPending ? t("generating") : t("generate")}
              </Button>
            </div>
          </CardContent>
        </Card>
      </ConsentGateBanner>
    </div>
  );
}
