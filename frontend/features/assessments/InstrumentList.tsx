"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  listInstruments,
  type InstrumentOut,
} from "@/lib/api/endpoints/assessments";
import {
  instrumentBlurbVi,
  instrumentNameVi,
} from "@/features/assessments/instrument-items";

/**
 * InstrumentList (architecture.md §3 `(app)/assessments`, FR-10). Lists the
 * active instruments (`GET /assessments`) client-side with the bearer token and
 * links each to its runner. The instrument list itself is not sensitive, so it
 * uses a normal cached query (the *results* are the sensitive surface, CP-3).
 */
export function InstrumentList() {
  const t = useTranslations("assessment");
  const { data, isLoading, isError } = useQuery<InstrumentOut[]>({
    queryKey: ["assessment-instruments"],
    queryFn: listInstruments,
  });

  if (isLoading) {
    return (
      <p role="status" className="text-sm text-ink-600">
        {t("loadingInstruments")}
      </p>
    );
  }

  if (isError || !data) {
    return (
      <p role="alert" className="text-sm text-danger-600">
        {t("loadInstrumentsError")}
      </p>
    );
  }

  const active = data.filter((instrument) => instrument.is_active);

  if (active.length === 0) {
    return <p className="text-sm text-ink-600">{t("noInstruments")}</p>;
  }

  return (
    <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {active.map((instrument) => (
        <li key={instrument.id}>
          <Card className="flex h-full flex-col">
            <CardHeader>
              <CardTitle>{instrumentNameVi(instrument.type)}</CardTitle>
              <CardDescription>
                {instrumentBlurbVi(instrument.type)}
              </CardDescription>
            </CardHeader>
            <CardContent className="mt-auto">
              <Button asChild>
                <Link href={`/assessments/${instrument.type}`}>
                  {t("startInstrument")}
                </Link>
              </Button>
            </CardContent>
          </Card>
        </li>
      ))}
    </ul>
  );
}
