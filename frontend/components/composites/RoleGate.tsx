"use client";

import { type ReactNode } from "react";
import { useTranslations } from "next-intl";

import { useAuthStore } from "@/lib/auth/store";

/**
 * Reusable client role guard (architecture.md §5.3, §7; CP-4). Restricts a
 * route segment to users who hold at least one of `roles`. The minimal contract
 * is shared with sibling role-gated slices (school-admin / [CRED_36D5F7BB]) so it stays
 * a single source of truth.
 *
 * Behaviour:
 *  - session `loading` (pre-bootstrap silent refresh) → render the shared
 *    loading copy; the guard never decides while the session is unknown.
 *  - authenticated but holding NONE of `roles` → render a neutral
 *    "no access" block. It does NOT redirect (no redirect loop with the
 *    `(app)` auth guard) and leaks no information about what exists (CP-4).
 *  - holds a required role → render `children`.
 *
 * The role claim comes from `useAuthStore().user.roles`, derived from the
 * access-token claims (`lib/auth/store.ts` → `rolesFromToken`). The backend
 * stays the final authority on every request (architecture.md §5.3); this gate
 * only prevents rendering links/fetches the user plainly cannot use.
 */
export function RoleGate({
  roles,
  children,
}: {
  readonly roles: readonly string[];
  readonly children: ReactNode;
}) {
  const t = useTranslations("common");
  const status = useAuthStore((s) => s.status);
  const userRoles = useAuthStore((s) => s.user?.roles);

  if (status === "loading") {
    return (
      <div
        className="flex min-h-[40vh] items-center justify-center px-4"
        data-role-gate="loading"
      >
        <p role="status" className="text-sm text-ink-600">
          {t("loading")}
        </p>
      </div>
    );
  }

  const allowed = (userRoles ?? []).some((role) => roles.includes(role));

  if (!allowed) {
    return (
      <div
        role="alert"
        data-role-gate="denied"
        className="mx-auto mt-10 max-w-lg rounded-md border border-input bg-surface p-6 text-center"
      >
        <p className="text-base font-semibold text-ink-900">
          {t("noAccessTitle")}
        </p>
        <p className="mt-2 text-sm text-ink-600">{t("noAccessDescription")}</p>
      </div>
    );
  }

  return <>{children}</>;
}
