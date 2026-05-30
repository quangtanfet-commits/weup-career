import { ProgressView } from "@/features/progress/ProgressView";

/**
 * Authenticated K-A-R progress route (architecture.md §3, §11; FR-20..24, CP-8).
 * A thin server entry that renders the client `ProgressView`: all personal
 * progress fetching happens client-side (token + consent gate live there), so
 * nothing sensitive enters the RSC cache (architecture.md §5.4).
 */
export default function ProgressPage() {
  return <ProgressView />;
}
