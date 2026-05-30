import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CareerSummary } from "@/lib/api/endpoints/careers";

/**
 * Presentational career card (architecture.md §4.4 — `CareerCard`). RSC-safe:
 * no client hooks, renders only the public summary fields and links to the
 * public detail page (`/careers/{id}`).
 */
export function CareerCard({ career }: { career: CareerSummary }) {
  return (
    <Card className="h-full transition-shadow hover:shadow-md">
      <CardHeader>
        <CardTitle>
          <Link
            href={`/careers/${encodeURIComponent(career.id)}`}
            className="text-ink-900 hover:text-primary-700 focus-visible:underline focus-visible:outline-none"
          >
            {career.name}
          </Link>
        </CardTitle>
        <p className="text-sm text-ink-600">{career.field}</p>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-2">
        {career.riasec_codes.map((code) => (
          <span
            key={code}
            className="rounded-full bg-primary-50 px-2.5 py-0.5 text-xs font-medium text-primary-700"
          >
            {code}
          </span>
        ))}
      </CardContent>
    </Card>
  );
}
