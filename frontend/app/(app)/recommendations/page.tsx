import { RecommendationsView } from "@/features/recommendations/RecommendationsView";

/**
 * Recommendations list/entry route (architecture.md §3 `(app)/recommendations`,
 * §10 L5; FR-60..62, CP-5/CP-6). A thin server entry that renders the client
 * `RecommendationsView`: all personal recommendation work happens client-side
 * (token + consent gate live there), so nothing enters the RSC cache
 * (architecture.md §5.4). The view is `[gate]` — it wraps the generate area in
 * the consent gate.
 */
export default function RecommendationsPage() {
  return <RecommendationsView />;
}
