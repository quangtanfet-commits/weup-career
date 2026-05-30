"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api/errors";
import { useConfirmRecommendation } from "./useRecommendations";
import type {
  RecoDecision,
  RecommendationOut,
} from "@/lib/api/endpoints/recommendations";

/**
 * HumanConfirmAction (architecture.md §4.4, §7 CP-5; FR-61/62). The explicit
 * accept / reject / later cluster that is the ONLY way a recommendation becomes
 * effective. There is no auto-apply and no optimistic update: the confirm call
 * fires only on a user click, and the resolved state comes from the backend
 * re-read (the hook invalidates the recommendation read on success).
 *
 * Decisions map 1:1 to the backend `RecoDecision` enum
 * (accepted/rejected/deferred). While a decision is in flight all buttons are
 * disabled so a learner cannot double-submit or race two decisions.
 */
const DECISIONS: readonly RecoDecision[] = ["accepted", "rejected", "deferred"];

export function HumanConfirmAction({
  recoId,
  onConfirmed,
}: {
  recoId: string;
  onConfirmed?: (reco: RecommendationOut) => void;
}) {
  const t = useTranslations("recommendations");
  const confirm = useConfirmRecommendation(recoId);
  const [pending, setPending] = useState<RecoDecision | null>(null);
  const [error, setError] = useState<string | null>(null);

  const decide = (decision: RecoDecision) => {
    setError(null);
    setPending(decision);
    confirm.mutate(
      { decision },
      {
        onSuccess: (reco) => {
          setPending(null);
          onConfirmed?.(reco);
        },
        onError: (err) => {
          setPending(null);
          setError(err instanceof ApiError ? err.message : t("genericError"));
        },
      },
    );
  };

  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-ink-600">{t("confirmPrompt")}</p>
      {error ? (
        <p role="alert" className="text-sm text-danger-600">
          {error}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-3">
        {DECISIONS.map((decision) => (
          <Button
            key={decision}
            type="button"
            variant={decision === "accepted" ? "default" : "outline"}
            disabled={confirm.isPending}
            onClick={() => decide(decision)}
          >
            {pending === decision
              ? t("confirmSubmitting")
              : t(`decision.${decision}`)}
          </Button>
        ))}
      </div>
    </div>
  );
}
