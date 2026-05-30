import { type ReactNode } from "react";

import { RoleGate } from "@/components/composites/RoleGate";

/**
 * School-admin segment guard (architecture.md §3, §10; FR-80, CP-4). Every
 * `/school-admin/*` page requires the `school_admin` role; non-admins see a
 * neutral "no access" block (the backend remains the final authority).
 */
export default function SchoolAdminLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <RoleGate roles={["school_admin"]}>{children}</RoleGate>;
}
