import Link from "next/link";
import { getTranslations } from "next-intl/server";

import { Button } from "@/components/ui/button";

export default async function HomePage() {
  const app = await getTranslations("app");
  const nav = await getTranslations("nav");
  return (
    <main className="mx-auto flex max-w-5xl flex-col items-start gap-6 px-4 py-16">
      <h1 className="text-4xl font-bold text-ink-900">{app("name")}</h1>
      <p className="max-w-2xl text-lg text-ink-600">{app("tagline")}</p>
      <Button asChild size="lg">
        <Link href="/careers">{nav("careers")}</Link>
      </Button>
    </main>
  );
}
