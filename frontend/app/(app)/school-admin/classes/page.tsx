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
import { ClassList } from "@/features/school/ClassList";
import { CreateClassForm } from "@/features/school/CreateClassForm";

/**
 * School-admin classes route (architecture.md §3, §10; FR-80, CP-4). Gated to
 * `school_admin` by the segment layout. Lists `GET /school/{id}/classes` and
 * creates classes via `POST /school/{id}/classes`.
 *
 * `UserOut`/`/auth/me` does not carry the admin's `school_id` (the school
 * channel is DB-relational, not a token claim — schema §SchoolRole), so the
 * page collects the `school_id` to scope its calls; the backend re-checks the
 * admin actually owns that school per request (CP-4), so an unauthorised id is
 * rejected server-side, not trusted from the input.
 */
export default function SchoolAdminClassesPage() {
  const t = useTranslations("schoolAdmin");
  const [schoolId, setSchoolId] = useState("");
  const trimmed = schoolId.trim();
  const activeSchoolId = trimmed.length > 0 ? trimmed : undefined;

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>{t("classes.pageTitle")}</CardTitle>
          <CardDescription>{t("classes.pageDescription")}</CardDescription>
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

      <Card>
        <CardHeader>
          <CardTitle>{t("classes.listTitle")}</CardTitle>
          <CardDescription>{t("classes.listDescription")}</CardDescription>
        </CardHeader>
        <CardContent>
          <ClassList schoolId={activeSchoolId} />
        </CardContent>
      </Card>

      {activeSchoolId ? (
        <Card>
          <CardHeader>
            <CardTitle>{t("createClass.title")}</CardTitle>
            <CardDescription>{t("createClass.description")}</CardDescription>
          </CardHeader>
          <CardContent>
            <CreateClassForm schoolId={activeSchoolId} />
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
