"use client";

import { useTranslations } from "next-intl";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { RoleGate } from "@/components/composites/RoleGate";
import { ChildrenPanel } from "@/features/account/ChildrenPanel";

/**
 * Guardian children route (architecture.md §11; FR-92, Law 91/2025). Gated to
 * the `guardian` role — a guardian exercises a linked child's data-subject
 * rights (per-child export + soft-delete). Non-guardians see the neutral
 * "no access" block; the backend re-checks the guardian link per request (CP-4).
 */
export default function AccountChildrenPage() {
  const t = useTranslations("account");
  return (
    <RoleGate roles={["guardian"]}>
      <Card>
        <CardHeader>
          <CardTitle>{t("children.pageTitle")}</CardTitle>
          <CardDescription>{t("children.pageDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          <ChildrenPanel />
        </CardContent>
      </Card>
    </RoleGate>
  );
}
