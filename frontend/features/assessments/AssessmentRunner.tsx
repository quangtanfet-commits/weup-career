"use client";

import { useMemo, useState } from "react";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import { submitAssessment } from "@/lib/api/endpoints/assessments";
import type { InstrumentType } from "@/lib/api/endpoints/assessments";
import { ApiError } from "@/lib/api/errors";
import {
  itemsFor,
  instrumentNameVi,
  LIKERT_LABELS_VI,
  LIKERT_MAX,
  LIKERT_MIN,
} from "@/features/assessments/instrument-items";

/**
 * AssessmentRunner (architecture.md §4.4, FR-10/11; a11y §8). Steps the learner
 * through Likert items one screen at a time with a progress indicator and an
 * `aria-live` announcement of progress. Answers live in component memory only —
 * never localStorage — because the produced result is sensitive (CP-3). On
 * submit it POSTs answers and hands the new result id back to the page via
 * `onSubmitted` so it can route to the (no-cache) result view.
 */
export interface AssessmentRunnerProps {
  readonly instrumentType: InstrumentType;
  /** Called with the created result id after a successful submit (FR-11/15). */
  readonly onSubmitted: (resultId: string) => void;
}

const LIKERT_VALUES = Array.from(
  { length: LIKERT_MAX - LIKERT_MIN + 1 },
  (_, i) => LIKERT_MIN + i,
);

export function AssessmentRunner({
  instrumentType,
  onSubmitted,
}: AssessmentRunnerProps) {
  const t = useTranslations("assessment");
  const items = useMemo(() => itemsFor(instrumentType), [instrumentType]);

  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [index, setIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const total = items.length;
  const current = items[index];
  const answeredCount = Object.keys(answers).length;
  const allAnswered = answeredCount === total;
  const isLast = index === total - 1;

  function choose(value: number) {
    if (!current) return;
    setAnswers((prev) => ({ ...prev, [current.key]: value }));
  }

  function goNext() {
    if (!isLast) setIndex((i) => Math.min(i + 1, total - 1));
  }

  function goPrev() {
    setIndex((i) => Math.max(i - 1, 0));
  }

  async function onSubmit() {
    setSubmitError(null);
    setSubmitting(true);
    try {
      const result = await submitAssessment(instrumentType, { answers });
      onSubmitted(result.id);
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.message : t("submitError"));
      setSubmitting(false);
    }
  }

  if (!current) {
    return (
      <p role="alert" className="text-sm text-danger-600">
        {t("noItems")}
      </p>
    );
  }

  const selected = answers[current.key];

  return (
    <section
      role="group"
      aria-label={instrumentNameVi(instrumentType)}
      className="flex flex-col gap-6"
    >
      <div>
        <div
          aria-live="polite"
          className="text-sm font-medium text-ink-600"
          data-testid="runner-progress"
        >
          {t("progress", { current: index + 1, total })}
        </div>
        <div
          className="mt-2 h-2 w-full overflow-hidden rounded-full bg-primary-50"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={total}
          aria-valuenow={answeredCount}
          aria-label={t("progressBarLabel")}
        >
          <div
            className="h-full bg-secondary-500 transition-[width]"
            style={{ width: `${(answeredCount / total) * 100}%` }}
          />
        </div>
      </div>

      <fieldset className="flex flex-col gap-4">
        <legend className="text-lg font-semibold text-ink-900">
          {current.prompt_vi}
        </legend>
        <div className="flex flex-col gap-2">
          {LIKERT_VALUES.map((value) => {
            const id = `${current.key}-${value}`;
            return (
              <label
                key={id}
                htmlFor={id}
                className="flex cursor-pointer items-center gap-3 rounded-md border border-input bg-white px-4 py-3 text-sm text-ink-900 hover:bg-primary-50 has-[:checked]:border-primary-600 has-[:checked]:bg-primary-50"
              >
                <input
                  type="radio"
                  id={id}
                  name={current.key}
                  value={value}
                  checked={selected === value}
                  onChange={() => choose(value)}
                  className="h-4 w-4"
                />
                <span>{LIKERT_LABELS_VI[value - 1]}</span>
              </label>
            );
          })}
        </div>
      </fieldset>

      {submitError ? (
        <p role="alert" className="text-sm text-danger-600">
          {submitError}
        </p>
      ) : null}

      <p className="text-xs text-ink-600" id="runner-sensitive-note">
        {t("resultSensitiveNote")}
      </p>

      <div className="flex items-center justify-between gap-3">
        <Button
          type="button"
          variant="outline"
          onClick={goPrev}
          disabled={index === 0 || submitting}
        >
          {t("prev")}
        </Button>

        {isLast ? (
          <Button
            type="button"
            onClick={onSubmit}
            disabled={!allAnswered || submitting}
            aria-describedby="runner-sensitive-note"
          >
            {submitting ? t("submitting") : t("submit")}
          </Button>
        ) : (
          <Button
            type="button"
            onClick={goNext}
            disabled={selected === undefined}
          >
            {t("next")}
          </Button>
        )}
      </div>
    </section>
  );
}
