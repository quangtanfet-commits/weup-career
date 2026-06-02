"use client";

import { useTranslations } from "next-intl";

import { useSupportRequests } from "@/features/wellbeing/useWellbeing";
import { type SupportRequestStatus } from "@/lib/api/endpoints/wellbeing";
import { ApiError } from "@/lib/api/errors";

const STATUS_TOKENS: Record<SupportRequestStatus, string> = {
  open: "border-warning-600/40 bg-warning-600/10 text-warning-600",
  acknowledged: "border-secondary-700/30 bg-primary-50 text-secondary-700",
  closed: "border-input bg-surface text-ink-600",
};

/**
 * The signed-in learner's own support requests (architecture.md §4, FR-71).
 *
 * Lists prior referrals with their **routing** status only — `open`,
 * `acknowledged`, `closed` — which tracks where the referral is in reaching a
 * counselor, never any health/risk state (NG-03, no diagnosis). The status is
 * conveyed with text (not colour alone) for a11y (architecture.md §8).
 *
 * Reads through TanStack Query (ADR-004); the create mutation invalidates the
 * list key so a new request appears without the parent coordinating a refresh.
 * Fetches on the client with the in-memory bearer token (no caching of personal
 * data into the RSC layer).
 */
export function SupportRequestList() {
  const t = useTranslations("wellbeing");
  const { data, isPending, isError, error } = useSupportRequests();

  if (isError) {
    return (
      <p role="alert" className="text-sm text-danger-600">
        {error instanceof ApiError ? error.message : t("genericError")}
      </p>
    );
  }

  if (isPending) {
    return (
      <p role="status" className="text-sm text-ink-600">
        {t("listLoading")}
      </p>
    );
  }

  if (data.length === 0) {
    return <p className="text-sm text-ink-600">{t("listEmpty")}</p>;
  }

  const formatter = new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "medium",
    timeStyle: "short",
  });

  return (
    <ul className="flex flex-col gap-3">
      {data.map((item) => (
        <li
          key={item.id}
          className="flex flex-col gap-1.5 rounded-md border border-input p-4"
        >
          <div className="flex items-center justify-between gap-3">
            <span className="text-xs text-ink-600">
              {formatter.format(new Date(item.created_at))}
            </span>
            <span
              className={`rounded-full border px-2 py-0.5 text-xs font-medium ${STATUS_TOKENS[item.status]}`}
            >
              {t(`status.${item.status}`)}
            </span>
          </div>
          <p className="whitespace-pre-wrap text-sm text-ink-900">
            {item.message}
          </p>
        </li>
      ))}
    </ul>
  );
}
