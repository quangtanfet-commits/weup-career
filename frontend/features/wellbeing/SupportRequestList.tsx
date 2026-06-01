"use client";

import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";

import {
  listSupportRequests,
  type SupportRequestOut,
  type SupportRequestStatus,
} from "@/lib/api/endpoints/wellbeing";
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
 * Re-fetches whenever `refreshKey` changes so the parent page can refresh the
 * list after a new request is created. Fetches on the client with the in-memory
 * bearer token (no caching of personal data into the RSC layer).
 */
export function SupportRequestList({
  refreshKey = 0,
}: {
  refreshKey?: number;
}) {
  const t = useTranslations("wellbeing");
  const [items, setItems] = useState<SupportRequestOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setItems(await listSupportRequests());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("genericError"));
    }
  }, [t]);

  useEffect(() => {
    // Client fetch-on-mount/refresh: `load` resets error state synchronously
    // then setState after an awaited fetch. This is the data-load pattern that
    // react-query (already a dep) would replace; migrating these feature reads
    // is tracked separately, out of scope for the Next 16 bump.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load, refreshKey]);

  if (error) {
    return (
      <p role="alert" className="text-sm text-danger-600">
        {error}
      </p>
    );
  }

  if (items === null) {
    return (
      <p role="status" className="text-sm text-ink-600">
        {t("listLoading")}
      </p>
    );
  }

  if (items.length === 0) {
    return <p className="text-sm text-ink-600">{t("listEmpty")}</p>;
  }

  const formatter = new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "medium",
    timeStyle: "short",
  });

  return (
    <ul className="flex flex-col gap-3">
      {items.map((item) => (
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
