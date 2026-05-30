import Link from "next/link";
import { getTranslations } from "next-intl/server";

import { Button } from "@/components/ui/button";

export default async function NotFound() {
  const t = await getTranslations("notFound");
  return (
    <main className="mx-auto flex min-h-[60vh] max-w-xl flex-col items-center justify-center gap-4 px-4 text-center">
      <h1 className="text-3xl font-bold">{t("title")}</h1>
      <p className="text-ink-600">{t("description")}</p>
      <Button asChild>
        <Link href="/">{t("backHome")}</Link>
      </Button>
    </main>
  );
}
