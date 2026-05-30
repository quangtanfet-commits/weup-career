"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { FormField } from "@/components/composites/FormField";
import { AssignMemberForm } from "@/features/school/AssignMemberForm";

/**
 * School-admin members route (architecture.md §3, §10; FR-80, CP-4). Gated to
 * `school_admin` by the segment layout. Assigns students/counselors via
 * `POST /school/{id}/members`.
 *
 * As with the classes page, the admin's `school_id` is not in the session
 * (DB-relational, not a token claim), so it is collected here; the backend
 * re-checks ownership per request (CP-4), so an unauthorised id is rejected
 * server-side rather than trusted from the input.
 */
export default function SchoolAdminMembersPage() {
  const t = useTranslations("schoolAdmin");
  const [schoolId, setSchoolId] = useState("");
  const trimmed = schoolId.trim();
  const activeSchoolId = trimmed.length > 0 ? trimmed : undefined;

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("members.pageTitle")}</CardTitle>
          <CardDescription>{t("members.pageDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          <FormField
            id="school-id"
            label={t("schoolIdLabel")}
            hint={t("schoolIdHint")}
          >
            <Input
              value={schoolId}
              onChange={(e) => setSchoolId(e.target.value)}
            />
          </FormField>
        </CardContent>
      </Card>

      {activeSchoolId ? (
        <Card>
          <CardHeader>
            <CardTitle>{t("assignMember.title")}</CardTitle>
            <CardDescription>{t("assignMember.description")}</CardDescription>
          </CardHeader>
          <CardContent>
            <AssignMemberForm schoolId={activeSchoolId} />
          </CardContent>
        </Card>
      ) : (
        <p className="text-sm text-ink-600">{t("members.needSchool")}</p>
      )}
    </div>
  );
}
