import Link from "next/link";
import { getTranslations } from "next-intl/server";

/**
 * Auth route-group layout (architecture.md §3) — login/register live here with
 * no token. Centered card chrome; the actual forms (RHF + Zod) are built in the
 * F1 auth pages. F1 ships the layout + placeholders so the route group exists.
 */
export default async function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const app = await getTranslations("app");
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 px-4">
      <Link href="/" className="text-xl font-semibold text-primary-700">
        {app("name")}
      </Link>
      <div className="w-full max-w-sm">{children}</div>
    </div>
  );
}
