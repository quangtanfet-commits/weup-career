import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { CareerSummary } from "@/lib/api/endpoints/careers";

/**
 * Presentational career card (architecture.md §4.4 — `CareerCard`). RSC-safe:
 * no client hooks, renders only the public summary fields.
 */
export function CareerCard({ career }: { career: CareerSummary }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{career.name}</CardTitle>
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
