import Link from "next/link";
import { getTranslations } from "next-intl/server";

/**
 * Public route-group layout (architecture.md §3). Server-rendered chrome for
 * anonymous, SEO-facing pages (career library, content, marketing). No session
 * dependency — these routes never require a token.
 */
export default async function PublicLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const t = await getTranslations("nav");
  const app = await getTranslations("app");
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b bg-white">
        <nav className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
          <Link href="/" className="font-semibold text-primary-700">
            {app("name")}
          </Link>
          <ul className="flex items-center gap-6 text-sm">
            <li>
              <Link href="/nghe-nghiep" className="hover:text-primary-700">
                {t("careers")}
              </Link>
            </li>
            <li>
              <Link href="/login" className="hover:text-primary-700">
                {t("login")}
              </Link>
            </li>
          </ul>
        </nav>
      </header>
      <div className="flex-1">{children}</div>
      <footer className="border-t bg-white py-6 text-center text-sm text-ink-600">
        {app("name")} — {app("tagline")}
      </footer>
    </div>
  );
}
