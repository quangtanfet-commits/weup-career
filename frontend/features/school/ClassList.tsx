"use client";

import { useTranslations } from "next-intl";

import { useClasses } from "@/features/school/useSchool";
import { ApiError } from "@/lib/api/errors";

/**
 * Classes in the admin's school (architecture.md §10; FR-80). Reads
 * `GET /school/{id}/classes` on the client with the bearer token. Until a
 * `schoolId` is provided the query is disabled and a prompt is shown, so the
 * page can ask the admin which school to manage without firing an unscoped call
 * (CP-4 — the FE never guesses a school).
 */
export function ClassList({ schoolId }: { schoolId: string | undefined }) {
  const t = useTranslations("schoolAdmin");
  const { data, isPending, isError, error } = useClasses(schoolId);

  if (!schoolId) {
    return <p className="text-sm text-ink-600">{t("classes.needSchool")}</p>;
  }

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
        {t("classes.loading")}
      </p>
    );
  }

  if (data.length === 0) {
    return <p className="text-sm text-ink-600">{t("classes.empty")}</p>;
  }

  return (
    <ul className="flex flex-col gap-3">
      {data.map((cls) => (
        <li
          key={cls.id}
          className="flex items-center justify-between gap-3 rounded-md border border-input p-4"
        >
          <span className="text-sm font-medium text-ink-900">{cls.name}</span>
          <span className="rounded-full border border-input px-2 py-0.5 text-xs text-ink-600">
            {t("classes.gradeLabel", { grade: cls.grade })}
          </span>
        </li>
      ))}
    </ul>
  );
}
