import { type ReactNode } from "react";

import { RoleGate } from "@/components/composites/RoleGate";

/**
 * Content-editor segment guard (architecture.md §3, §10; FR-90, CP-4). Every
 * `/editor/*` page requires the `content_editor` role; others see a neutral
 * "no access" block (the backend remains the final authority).
 */
export default function EditorLayout({ children }: { children: ReactNode }) {
  return <RoleGate roles={["content_editor"]}>{children}</RoleGate>;
}
