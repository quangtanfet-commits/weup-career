"use client";

import { useTranslations } from "next-intl";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { HumanConfirmAction } from "./HumanConfirmAction";
import { RationalePanel } from "./RationalePanel";
import type {
  RecoDecision,
  RecommendationOut,
} from "@/lib/api/endpoints/recommendations";

const DECISION_TOKENS: Record<RecoDecision, string> = {
  accepted: "border-success-600/40 bg-success-600/10 text-success-600",
  rejected: "border-danger-600/40 bg-danger-600/10 text-danger-600",
  deferred: "border-warning-600/40 bg-warning-600/10 text-warning-600",
};

/**
 * Render the recommendation `payload` as a readable list. The backend payload
 * is an open key→value map (FR-60), so we show each entry as a labelled row;
 * primitive values are stringified, structured values are JSON-rendered. This
 * keeps the card faithful to whatever the engine returned without inventing
 * fields the FE doesn't own.
 */
function PayloadList({ payload }: { payload: Record<string, unknown> }) {
  const entries = Object.entries(payload);
  if (entries.length === 0) return null;
  return (
    <dl className="flex flex-col gap-2">
      {entries.map(([key, value]) => (
        <div key={key} className="flex flex-col gap-0.5">
          <dt className="text-xs font-medium uppercase tracking-wide text-ink-600">
            {key}
          </dt>
          <dd className="whitespace-pre-wrap text-sm text-ink-900">
            {typeof value === "string" ? value : JSON.stringify(value)}
          </dd>
        </div>
      ))}
    </dl>
  );
}

/**
 * RecommendationCard (architecture.md §4.4, §7 CP-5/CP-6; FR-61/62).
 *
 * CP-6 — `RationalePanel` is a MANDATORY part of the card. If the recommendation
 * arrives without a non-empty `rationale` we treat it as a data error and render
 * an explicit error state; we never render a blank "no reason" card.
 *
 * CP-5 — an unconfirmed recommendation is clearly labelled "chưa có hiệu lực"
 * and only `HumanConfirmAction` can confirm it; there is no auto-apply and no
 * optimistic state. Once confirmed, the recorded human decision is shown
 * (accepted/rejected/deferred) and the action cluster is no longer offered.
 * The card always carries the "the decision is yours/your guardian's/your
 * counselor's" notice (FR-62).
 */
export function RecommendationCard({
  recommendation,
  onConfirmed,
}: {
  recommendation: RecommendationOut;
  onConfirmed?: (reco: RecommendationOut) => void;
}) {
  const t = useTranslations("recommendations");

  // CP-6: a recommendation without a real rationale is a data error.
  const rationale = recommendation.rationale?.trim();
  if (!rationale) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t("cardTitle")}</CardTitle>
        </CardHeader>
        <CardContent>
          <p
            role="alert"
            className="rounded-md border border-danger-600/40 bg-danger-600/10 p-4 text-sm text-danger-600"
          >
            {t("rationaleMissing")}
          </p>
        </CardContent>
      </Card>
    );
  }

  const decision = recommendation.confirmed_decision;
  const isConfirmed = decision !== null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("cardTitle")}</CardTitle>
        <CardDescription>{t("cardDescription")}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <PayloadList
          payload={recommendation.payload as Record<string, unknown>}
        />

        {/* CP-6: rationale is always present on the card. */}
        <RationalePanel rationale={rationale} />

        {/* FR-62: the decision belongs to the human, the system never enforces it. */}
        <p className="rounded-md border border-warning-600/40 bg-warning-600/10 p-3 text-sm text-warning-600">
          {t("decisionIsYours")}
        </p>

        {isConfirmed ? (
          <p
            role="status"
            className={`rounded-md border px-3 py-2 text-sm font-medium ${DECISION_TOKENS[decision]}`}
          >
            {t("confirmedState", { decision: t(`decision.${decision}`) })}
          </p>
        ) : (
          <>
            {/* CP-5: an unconfirmed recommendation is clearly not yet effective. */}
            <p
              role="status"
              className="rounded-md border border-input bg-surface px-3 py-2 text-sm text-ink-600"
            >
              {t("notEffective")}
            </p>
            <HumanConfirmAction
              recoId={recommendation.id}
              onConfirmed={onConfirmed}
            />
          </>
        )}
      </CardContent>
    </Card>
  );
}
