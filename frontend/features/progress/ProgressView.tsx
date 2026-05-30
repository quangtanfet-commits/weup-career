"use client";

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
import { useCompetencies, useMyProgress } from "./useProgress";
import { CompetencyTree } from "./CompetencyTree";
import { DevPhasePanel } from "./DevPhasePanel";
import { KARProgressViz } from "./KARProgressViz";

/**
 * F4 progress page body (architecture.md §11, FR-20..24, CP-8). Client-rendered
 * inside the guarded `(app)` group so personal progress never enters the RSC
 * cache (architecture.md §5.4). Consent-gated for children <16 (CP-1/CP-2): the
 * `ConsentGateBanner` short-circuits to a CTA before any authed fetch matters.
 *
 * Two reads drive the view: the fixed competency tree (`useCompetencies`) and
 * the learner's coordinates (`useMyProgress`). The tree renders even with no
 * progress yet; the K-A-R viz + dev-phase panel reflect achieved depth.
 */
export function ProgressView() {
  const t = useTranslations("progress");
  const common = useTranslations("common");
  const competencies = useCompetencies();
  const progress = useMyProgress();

  const isLoading = competencies.isLoading || progress.isLoading;
  const isError = competencies.isError || progress.isError;

  const competencyItems = competencies.data ?? [];
  const progressItems = progress.data ?? [];

  return (
    <ConsentGateBanner>
      <div className="flex flex-col gap-6">
        <header className="flex flex-col gap-1">
          <h1 className="text-2xl font-bold text-ink-900">{t("title")}</h1>
          <p className="text-sm text-ink-600">{t("subtitle")}</p>
        </header>

        {isLoading ? (
          <p role="status" className="text-sm text-ink-600">
            {t("loading")}
          </p>
        ) : isError ? (
          <div
            role="alert"
            className="flex flex-col items-start gap-3 rounded-md border border-danger-600/40 bg-danger-600/10 p-5"
          >
            <p className="text-sm text-danger-600">{t("loadError")}</p>
            <Button
              variant="outline"
              onClick={() => {
                void competencies.refetch();
                void progress.refetch();
              }}
            >
              {common("retry")}
            </Button>
          </div>
        ) : (
          <div className="flex flex-col gap-6">
            <Card>
              <CardHeader>
                <CardTitle>{t("overviewHeading")}</CardTitle>
                <CardDescription>{t("overviewDescription")}</CardDescription>
              </CardHeader>
              <CardContent>
                <KARProgressViz items={progressItems} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t("devPhaseHeading")}</CardTitle>
                <CardDescription>{t("devPhaseDescription")}</CardDescription>
              </CardHeader>
              <CardContent>
                <DevPhasePanel items={progressItems} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t("treeHeading")}</CardTitle>
                <CardDescription>{t("treeDescription")}</CardDescription>
              </CardHeader>
              <CardContent>
                <CompetencyTree
                  competencies={competencyItems}
                  progress={progressItems}
                />
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </ConsentGateBanner>
  );
}
