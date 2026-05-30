import { type ReactNode } from "react";

import { RoleGate } from "@/components/composites/RoleGate";

/**
 * Role guard for the `/counselor/*` segment (architecture.md §3, §5.3, §7;
 * CP-4). The parent `(app)/layout.tsx` only distinguishes authenticated vs
 * anonymous; this layer additionally requires the `counselor` role. A signed-in
 * user without it sees a neutral "no access" block (no info leak, no redirect
 * loop). The backend remains the final authority (403/404) on every request.
 */
export default function CounselorLayout({ children }: { children: ReactNode }) {
  return <RoleGate roles={["counselor"]}>{children}</RoleGate>;
}
