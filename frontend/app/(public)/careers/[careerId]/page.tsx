import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { CareerDetail } from "@/features/careers/CareerDetail";
import { ApiError } from "@/lib/api/errors";
import {
  getCareer,
  type CareerDetail as CareerDetailData,
} from "@/lib/api/endpoints/careers";

/**
 * Public career detail (Luồng 3, Điều 5(a)) — architecture.md §3
 * `(public)/careers/[careerId]`.
 *
 * **React Server Component**: fetches `GET /api/v1/careers/{id}` anonymously
 * (no token, BE-1; published-only). A 404 from the backend becomes the neutral
 * Next.js not-found page (CP-4 — existence-hiding, no leak about the id).
 */
type PageProps = { params: Promise<{ careerId: string }> };

/** Fetch the career once, mapping a 404 to `null` for both metadata + render. */
async function loadCareer(careerId: string): Promise<CareerDetailData | null> {
  try {
    return await getCareer(careerId);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { careerId } = await params;
  const career = await loadCareer(careerId);
  if (!career) return { title: "Không tìm thấy nghề" };
  return {
    title: career.name,
    description: career.labor_market_outlook.slice(0, 160),
  };
}

export default async function CareerDetailPage({ params }: PageProps) {
  const { careerId } = await params;
  const t = await getTranslations("careers");
  const career = await loadCareer(careerId);

  if (!career) notFound();

  // Await the async child Server Component so the full tree resolves in one
  // pass (composition; also keeps the page unit-testable).
  const detailNode = await CareerDetail({ career });

  return (
    <main className="mx-auto max-w-4xl px-4 py-12">
      <Link
        href="/careers"
        className="text-sm font-medium text-primary-700 hover:underline"
      >
        ← {t("backToList")}
      </Link>
      {detailNode}
    </main>
  );
}
