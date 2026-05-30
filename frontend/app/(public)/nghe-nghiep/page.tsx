import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { CareerCard } from "@/features/careers/CareerCard";
import { listCareers, type CareerSummary } from "@/lib/api/endpoints/careers";

/**
 * Demo public career-library page (Luồng 3, Điều 5(a)).
 *
 * This is a **React Server Component**: it fetches `GET /api/v1/careers`
 * **anonymously** server-side via `listCareers()` (no Authorization header,
 * BE-1) and renders the titles. It proves the anonymous-RSC path — the backbone
 * of the public/sensitive split (architecture.md §3, §5.4). Published-only is
 * enforced server-side by the backend.
 */
export const metadata: Metadata = {
  title: "Thư viện nghề nghiệp",
  description:
    "Khám phá nghề nghiệp theo Điều 5(a) — thông tin công khai, không cần đăng nhập.",
};

// Cap the demo list so an empty/large dataset both render cleanly.
const MAX_VISIBLE = 60;

export default async function CareerLibraryPage() {
  const t = await getTranslations("careers");

  let careers: CareerSummary[] = [];
  let failed = false;
  try {
    careers = await listCareers();
  } catch {
    failed = true;
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-12">
      <h1 className="text-3xl font-bold text-ink-900">{t("title")}</h1>
      <p className="mt-2 max-w-2xl text-ink-600">{t("subtitle")}</p>

      {failed ? (
        <p role="alert" className="mt-8 text-danger-600">
          {t("loadError")}
        </p>
      ) : careers.length === 0 ? (
        <p className="mt-8 text-ink-600">{t("empty")}</p>
      ) : (
        <ul className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {careers.slice(0, MAX_VISIBLE).map((career) => (
            <li key={career.id}>
              <CareerCard career={career} />
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
